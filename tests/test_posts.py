import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.config import Config
from app.main import app
from app.models import Base

# Используем основную БД
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TEST_POST = {
    "rutracker_id": "test_id_123",
    "link": "http://test.example.com",
    "title": "Test Post",
    "seeds": 10,
    "leaches": 5,
    "size": "1.2GB"
}

@pytest.fixture(scope="session", autouse=True)
def prepare_tables():
    """Создаем таблицы перед всеми тестами (если их нет)"""
    Base.metadata.create_all(engine)
    yield
    # Дополнительная очистка после всех тестов (опционально)
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE rutracker_posts RESTART IDENTITY CASCADE"))
        conn.commit()

@pytest.fixture
def db_session():
    """Сессия с откатом изменений после теста"""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()  # Откатываем все изменения теста
    connection.close()

@pytest.fixture
def client():
    """Тестовый клиент FastAPI"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def test_post_id(db_session):
    """Фикстура создает тестовый пост и возвращает его ID"""
    result = db_session.execute(text("""
        INSERT INTO rutracker_posts 
        (rutracker_id, link, title, seeds, leaches, size) 
        VALUES (:rutracker_id, :link, :title, :seeds, :leaches, :size)
        RETURNING id
    """), TEST_POST)
    db_session.commit()
    return result.fetchone()[0]

# Тесты для прямых SQL-запросов
def test_get_all_posts(db_session, test_post_id):
    posts = db_session.execute(text("SELECT * FROM rutracker_posts")).fetchall()
    assert any(post.id == test_post_id for post in posts)

def test_get_post_by_id(db_session, test_post_id):
    post = db_session.execute(
        text("SELECT * FROM rutracker_posts WHERE id = :id"),
        {"id": test_post_id}
    ).fetchone()
    assert post.title == TEST_POST["title"]

def test_update_post(db_session, test_post_id):
    """Тест прямого SQL-обновления"""
    updated_data = {
        "title": "SQL Updated Title",
        "seeds": 99
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
    
    assert updated_post.title == "SQL Updated Title"
    assert updated_post.seeds == 99

def test_delete_post(db_session, test_post_id):
    """Тест прямого SQL-удаления"""
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

# API-тесты
def test_api_get_all_posts(client, test_post_id):
    response = client.get("/posts/")
    assert response.status_code == 200
    assert any(p["id"] == test_post_id for p in response.json())

def test_api_get_post_by_id(client, test_post_id):
    response = client.get(f"/posts/{test_post_id}")
    assert response.status_code == 200
    assert response.json()["title"] == TEST_POST["title"]

def test_api_update_post(client, test_post_id):
    updated_data = {**TEST_POST, "title": "Updated Title"}
    response = client.put(f"/posts/{test_post_id}", json=updated_data)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"

def test_api_delete_post(client, test_post_id):
    response = client.delete(f"/posts/{test_post_id}")
    assert response.status_code == 200
    response = client.get(f"/posts/{test_post_id}")
    assert response.status_code == 404