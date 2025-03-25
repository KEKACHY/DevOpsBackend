import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.config import Config
from app.main import app

# Используем основную базу данных
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
    """Сессия для каждого теста с откатом изменений"""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client():
    """Тестовый клиент FastAPI"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def test_post_id(db_session):
    """Создает тестовый пост и возвращает его ID"""
    result = db_session.execute(text("""
        INSERT INTO rutracker_posts 
        (rutracker_id, link, title, seeds, leaches, size) 
        VALUES (:rutracker_id, :link, :title, :seeds, :leaches, :size)
        RETURNING id
    """), TEST_POST)
    db_session.commit()
    return result.fetchone()[0]

def test_get_all_posts(db_session, test_post_id):
    """Тест получения всех постов"""
    posts = db_session.execute(text("SELECT * FROM rutracker_posts")).fetchall()
    assert len(posts) >= 1  # Проверяем, что есть хотя бы наш тестовый пост

def test_get_post_by_id(db_session, test_post_id):
    """Тест получения поста по ID"""
    post = db_session.execute(
        text("SELECT * FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    ).fetchone()
    assert post is not None
    assert post.rutracker_id == TEST_POST["rutracker_id"]

def test_update_post(db_session, test_post_id):
    """Тест обновления поста"""
    updated_data = {
        "title": "Updated Title",
        "seeds": 20
    }
    
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
    
    assert updated_post.title == updated_data["title"]
    assert updated_post.seeds == updated_data["seeds"]

def test_delete_post(db_session, test_post_id):
    """Тест удаления поста"""
    # Проверяем, что пост существует перед удалением
    post = db_session.execute(
        text("SELECT 1 FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    ).fetchone()
    assert post is not None
    
    # Удаляем пост
    db_session.execute(
        text("DELETE FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    )
    db_session.commit()
    
    # Проверяем, что пост удален
    deleted_post = db_session.execute(
        text("SELECT 1 FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    ).fetchone()
    assert deleted_post is None

# API тесты
def test_api_get_all_posts(client, test_post_id):
    """Тест API получения всех постов"""
    response = client.get("/posts/")
    assert response.status_code == 200
    assert any(post["id"] == test_post_id for post in response.json())

def test_api_get_post_by_id(client, test_post_id):
    """Тест API получения поста по ID"""
    response = client.get(f"/posts/{test_post_id}")
    assert response.status_code == 200
    assert response.json()["id"] == test_post_id

def test_api_update_post(client, test_post_id):
    """Тест API обновления поста"""
    updated_data = {
        "rutracker_id": "updated_id",
        "link": "http://updated.example.com",
        "title": "Updated Post",
        "seeds": 30,
        "leaches": 10,
        "size": "2.5GB"
    }
    response = client.put(f"/posts/{test_post_id}", json=updated_data)
    assert response.status_code == 200
    assert response.json()["title"] == updated_data["title"]

def test_api_delete_post(client, test_post_id):
    """Тест API удаления поста"""
    response = client.delete(f"/posts/{test_post_id}")
    assert response.status_code == 200
    
    response = client.get(f"/posts/{test_post_id}")
    assert response.status_code == 404