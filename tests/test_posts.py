import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.config import Config
from app.main import app
from app import models  # Импортируем models для переопределения SessionLocal

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
    
    # Временное переопределение SessionLocal для зависимостей FastAPI
    original_session_local = models.SessionLocal
    models.SessionLocal = lambda: session
    
    yield session
    
    # Восстанавливаем оригинальный SessionLocal
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
        INSERT INTO rutracker_posts 
        (rutracker_id, link, title, seeds, leaches, size) 
        VALUES (:rutracker_id, :link, :title, :seeds, :leaches, :size)
        RETURNING id
    """), TEST_POST)
    db_session.commit()
    return result.fetchone()[0]


# ТЕСТЫ ДЛЯ RAW SQL ОПЕРАЦИЙ
def test_sql_create_post(db_session):
    """Тест создания записи через SQL"""
    result = db_session.execute(text("""
        INSERT INTO rutracker_posts 
        (rutracker_id, link, title, seeds, leaches, size) 
        VALUES (:rutracker_id, :link, :title, :seeds, :leaches, :size)
        RETURNING id
    """), TEST_POST)
    db_session.commit()
    post_id = result.fetchone()[0]
    assert post_id > 0

def test_sql_get_all_posts(db_session, test_post_id):
    """Тест получения всех записей через SQL"""
    posts = db_session.execute(text("SELECT * FROM rutracker_posts")).fetchall()
    assert any(post.id == test_post_id for post in posts)

def test_sql_get_post_by_id(db_session, test_post_id):
    """Тест получения одной записи через SQL"""
    post = db_session.execute(
        text("SELECT * FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    ).fetchone()
    assert post.title == TEST_POST["title"]

def test_sql_update_post(db_session, test_post_id):
    """Тест обновления записи через SQL"""
    updated_data = {"title": "Updated Title", "seeds": 99}
    
    db_session.execute(
        text("""
            UPDATE rutracker_posts 
            SET title = :title, seeds = :seeds 
            WHERE id = :id
        """),
        {**updated_data, "id": test_post_id}
    )
    db_session.commit()
    
    updated_post = db_session.execute(
        text("SELECT title, seeds FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    ).fetchone()
    
    assert updated_post.title == "Updated Title"
    assert updated_post.seeds == 99

def test_sql_delete_post(db_session, test_post_id):
    """Тест удаления записи через SQL"""
    # Проверяем существование перед удалением
    post = db_session.execute(
        text("SELECT 1 FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    ).fetchone()
    assert post is not None
    
    # Удаляем
    db_session.execute(
        text("DELETE FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    )
    db_session.commit()
    
    # Проверяем отсутствие
    deleted_post = db_session.execute(
        text("SELECT 1 FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    ).fetchone()
    assert deleted_post is None


# ТЕСТЫ ДЛЯ API
def test_api_create_post(client, db_session):
    """Тест создания записи через API"""
    response = client.post("/posts/", json=TEST_POST)
    assert response.status_code == 200
    assert response.json()["title"] == TEST_POST["title"]
    
    # Проверяем, что запись действительно создана в БД
    post_id = response.json()["id"]
    post = db_session.execute(
        text("SELECT 1 FROM rutracker_posts WHERE id = :id"),
        {"id": post_id}
    ).fetchone()
    assert post is not None

def test_api_get_all_posts(client, test_post_id):
    """Тест получения всех записей через API"""
    response = client.get("/posts/")
    assert response.status_code == 200
    posts = response.json()
    assert isinstance(posts, list)
    assert any(p["id"] == test_post_id for p in posts)

def test_api_get_post_by_id(client, test_post_id):
    """Тест получения одной записи через API"""
    response = client.get(f"/posts/{test_post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_post_id
    assert data["title"] == TEST_POST["title"]

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
    assert response.status_code == 200
    assert response.json()["title"] == "API Updated Title"

def test_api_delete_post(client, test_post_id, db_session):
    """Тест удаления записи через API"""
    # Проверяем, что пост существует перед удалением
    post = db_session.execute(
        text("SELECT 1 FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    ).fetchone()
    assert post is not None
    
    # Удаляем пост
    response = client.delete(f"/posts/{test_post_id}")
    assert response.status_code == 200
    
    # Проверяем, что пост действительно удален
    post = db_session.execute(
        text("SELECT 1 FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    ).fetchone()
    assert post is None