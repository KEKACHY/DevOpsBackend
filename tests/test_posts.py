import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.config import Config
from app.main import app
from app import models
from fastapi import status

# Настройка подключения к основной БД
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Тестовые данные
TEST_POST = {
    "rutracker_id": "test_id_123",
    "link": "http://test.example.com",
    "title": "Test Post",
    "seeds": 10,
    "leaches": 5,
    "size": "1.2GB"
}

@pytest.fixture
def db_session():
    """Фикстура для изолированной сессии с откатом изменений"""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    original_session_local = models.SessionLocal
    models.SessionLocal = lambda: session
    
    yield session
    
    models.SessionLocal = original_session_local
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client():
    """Фикстура для тестового клиента FastAPI"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def test_post_id(db_session):
    """Фикстура создаёт тестовый пост и возвращает его ID"""
    result = db_session.execute(text("""
        SELECT * FROM add_posts(
            :rutracker_id, :link, :title, :seeds, :leaches, :size
        )
    """), TEST_POST)
    db_session.commit()
    return result.fetchone()[0]

# ТЕСТЫ ДЛЯ API
def test_api_create_post(client, db_session):
    """Тест создания записи через API"""
    response = client.post("/posts/", json=TEST_POST)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["title"] == TEST_POST["title"]
    
    # Проверяем, что запись создана в БД
    post = db_session.execute(
        text("SELECT * FROM rutracker_posts WHERE rutracker_id = :rutracker_id"),
        {"rutracker_id": TEST_POST["rutracker_id"]}
    ).fetchone()
    assert post is not None

def test_api_create_duplicate_post(client, db_session):
    """Тест создания дубликата записи (должно обновиться)"""
    # Сначала создаем пост
    response1 = client.post("/posts/", json=TEST_POST)
    assert response1.status_code == status.HTTP_201_CREATED
    
    # Пытаемся создать с тем же rutracker_id, но другими данными
    updated_data = TEST_POST.copy()
    updated_data.update({
        "title": "Updated Title",
        "seeds": 99
    })
    
    response2 = client.post("/posts/", json=updated_data)
    assert response2.status_code == status.HTTP_201_CREATED
    
    # Проверяем, что данные обновились
    post = db_session.execute(
        text("SELECT title, seeds FROM rutracker_posts WHERE rutracker_id = :rutracker_id"),
        {"rutracker_id": TEST_POST["rutracker_id"]}
    ).fetchone()
    assert post.title == "Updated Title"
    assert post.seeds == 99

def test_api_get_all_posts(client, test_post_id):
    """Тест получения всех записей через API"""
    response = client.get("/posts/")
    assert response.status_code == status.HTTP_200_OK
    posts = response.json()
    assert isinstance(posts, list)
    assert any(p["id"] == test_post_id for p in posts)

def test_api_get_post_by_id(client, test_post_id):
    """Тест получения одной записи через API"""
    response = client.get(f"/posts/{test_post_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_post_id
    assert data["title"] == TEST_POST["title"]

def test_api_get_nonexistent_post(client):
    """Тест получения несуществующей записи"""
    response = client.get("/posts/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_api_update_post(client, test_post_id):
    """Тест обновления записи через API"""
    updated_data = {
        "rutracker_id": "updated_id",
        "link": "http://updated.example.com",
        "title": "API Updated Title",
        "seeds": 20,
        "leaches": 10,
        "size": "2.5GB"
    }
    response = client.put(f"/posts/{test_post_id}", json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "API Updated Title"

def test_api_update_nonexistent_post(client):
    """Тест обновления несуществующей записи"""
    response = client.put("/posts/999999", json=TEST_POST)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_api_delete_post(client, test_post_id, db_session):
    """Тест удаления записи через API"""
    # Проверяем существование поста
    response = client.get(f"/posts/{test_post_id}")
    assert response.status_code == status.HTTP_200_OK
    
    # Удаляем пост
    response = client.delete(f"/posts/{test_post_id}")
    assert response.status_code == status.HTTP_200_OK
    
    # Проверяем, что пост удален
    response = client.get(f"/posts/{test_post_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_api_delete_nonexistent_post(client):
    """Тест удаления несуществующей записи"""
    response = client.delete("/posts/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND