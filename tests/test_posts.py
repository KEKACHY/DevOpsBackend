import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Настройка тестовой базы данных
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

test_client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()

# Тест получения всех постов через API
def test_api_get_all_posts():
    response = test_client.get("/posts/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Тест создания нового поста через API
def test_api_create_post():
    new_post = {
        "rutracker_id": "test123",
        "link": "http://example.com",
        "title": "Test Post",
        "seeds": 10,
        "leaches": 5,
        "size": "700MB"
    }
    response = test_client.post("/posts/", json=new_post)
    assert response.status_code == 201
    data = response.json()
    assert data["rutracker_id"] == new_post["rutracker_id"]

# Тест получения поста по ID через API
def test_api_get_post_by_id():
    response = test_client.get("/posts/1")  # ID нужно уточнять в БД
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "rutracker_id" in response.json()

# Тест обновления поста через API
def test_api_update_post():
    updated_data = {
        "rutracker_id": "updated123",
        "link": "http://example.com/updated",
        "title": "Updated Post",
        "seeds": 20,
        "leaches": 10,
        "size": "1GB"
    }
    response = test_client.put("/posts/1", json=updated_data)  # ID уточняйте
    assert response.status_code in [200, 404]

# Тест удаления поста через API
def test_api_delete_post():
    response = test_client.delete("/posts/1")  # ID уточняйте
    assert response.status_code in [200, 404]