import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import uuid
from fastapi.testclient import TestClient

# Импорты из вашего приложения
from app.config import Config
from app.models import get_all_posts, get_post_by_id, update_post, delete_post
from app.main import app

TEST_DB_NAME = f"test_db_{uuid.uuid4().hex[:8]}"
MASTER_DB_URI = Config.SQLALCHEMY_DATABASE_URI
TEST_DB_URI = Config.SQLALCHEMY_DATABASE_URI.rsplit('/', 1)[0] + f"/{TEST_DB_NAME}"

TEST_POST = {
    "rutracker_id": "test_id_123",
    "link": "http://test.example.com",
    "title": "Test Post",
    "seeds": 10,
    "leaches": 5,
    "size": "1.2GB"
}

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    master_engine = None
    try:
        master_engine = create_engine(MASTER_DB_URI, isolation_level="AUTOCOMMIT")
        with master_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
        
        engine = create_engine(TEST_DB_URI)
        # Создаем таблицы (если используете SQLAlchemy ORM)
        # Base.metadata.create_all(engine)
        yield
        
    finally:
        if master_engine:
            engine.dispose()
            with master_engine.connect() as conn:
                conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
            master_engine.dispose()

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URI)
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture
def test_post_id(db_session):
    result = db_session.execute(text("""
        INSERT INTO rutracker_posts 
        (rutracker_id, link, title, seeds, leaches, size) 
        VALUES (:rutracker_id, :link, :title, :seeds, :leaches, :size)
        RETURNING id
    """), TEST_POST)
    db_session.commit()
    return result.fetchone()[0]

# ----- Тесты для функций models.py -----
def test_get_all_posts(db_session, test_post_id):
    posts = get_all_posts(db_session)
    assert isinstance(posts, list)
    assert len(posts) > 0
    assert any(post.rutracker_id == TEST_POST["rutracker_id"] for post in posts)

def test_get_post_by_id(db_session, test_post_id):
    post = get_post_by_id(db_session, test_post_id)
    assert post is not None
    assert post.rutracker_id == TEST_POST["rutracker_id"]
    assert post.title == TEST_POST["title"]

def test_update_post(db_session, test_post_id):
    updated_data = {
        "rutracker_id": "updated_id_456",
        "link": "http://updated.example.com",
        "title": "Updated Post",
        "seeds": 20,
        "leaches": 10,
        "size": "2.5GB"
    }
    update_post(db_session, test_post_id, **updated_data)
    
    updated_post = get_post_by_id(db_session, test_post_id)
    assert updated_post.rutracker_id == updated_data["rutracker_id"]
    assert updated_post.title == updated_data["title"]

def test_delete_post(db_session, test_post_id):
    # Убедимся, что пост существует перед удалением
    post = get_post_by_id(db_session, test_post_id)
    assert post is not None
    
    delete_post(db_session, test_post_id)
    
    deleted_post = get_post_by_id(db_session, test_post_id)
    assert deleted_post is None

# ----- Тесты для API endpoints -----
def test_api_get_all_posts(client, test_post_id):
    response = client.get("/posts/")
    assert response.status_code == 200
    posts = response.json()
    assert isinstance(posts, list)
    assert any(post["rutracker_id"] == TEST_POST["rutracker_id"] for post in posts)

def test_api_get_post_by_id(client, test_post_id):
    response = client.get(f"/posts/{test_post_id}")
    assert response.status_code == 200
    post = response.json()
    assert post["rutracker_id"] == TEST_POST["rutracker_id"]
    assert post["title"] == TEST_POST["title"]

def test_api_update_post(client, test_post_id):
    updated_data = {
        "rutracker_id": "updated_id_789",
        "link": "http://api-updated.example.com",
        "title": "API Updated Post",
        "seeds": 30,
        "leaches": 15,
        "size": "3.7GB"
    }
    response = client.put(f"/posts/{test_post_id}", json=updated_data)
    assert response.status_code == 200
    assert response.json()["title"] == updated_data["title"]

def test_api_delete_post(client, test_post_id):
    response = client.delete(f"/posts/{test_post_id}")
    assert response.status_code == 200
    
    response = client.get(f"/posts/{test_post_id}")
    assert response.status_code == 404