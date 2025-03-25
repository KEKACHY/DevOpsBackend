import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.config import engine, SessionLocal
from sqlalchemy import text

test_client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    db.begin()  # Явно начинаем транзакцию
    try:
        yield db
    finally:
        db.rollback()  # Явно откатываем
        db.close()

# Функция для генерации уникального rutracker_id
def generate_unique_rutracker_id():
    return str(uuid.uuid4())

# Тест создания нового поста через API
@pytest.fixture
def created_post(db_session):
    unique_rutracker_id = generate_unique_rutracker_id()
    new_post = {
        "rutracker_id": unique_rutracker_id,
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
    
    # Получаем ID созданного поста без коммита
    post_id = db_session.execute(
        text("""SELECT id FROM public.rutracker_posts WHERE rutracker_id = :rutracker_id"""),
        {"rutracker_id": new_post["rutracker_id"]}
    ).fetchone()[0]
    
    return post_id, new_post["rutracker_id"]

# Тест получения всех постов через API
def test_api_get_all_posts(db_session, created_post):
    response = test_client.get("/posts/")
    assert response.status_code == 200
    posts = response.json()
    assert isinstance(posts, list)
    assert len(posts) > 0

# Тест получения поста по ID через API
def test_api_get_post_by_id(db_session, created_post):
    post_id, rutracker_id = created_post
    response = test_client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    post_data = response.json()
    assert post_data["id"] == post_id
    assert post_data["rutracker_id"] == rutracker_id

# Тест обновления поста через API
def test_api_update_post(db_session, created_post):
    post_id, rutracker_id = created_post
    updated_data = {
        "rutracker_id": "updated123",
        "link": "http://example.com/updated",
        "title": "Updated Post",
        "seeds": 20,
        "leaches": 10,
        "size": "1GB"
    }
    response = test_client.put(f"/posts/{post_id}", json=updated_data)
    assert response.status_code == 200
    updated_post = response.json()
    assert updated_post["rutracker_id"] == updated_data["rutracker_id"]
    assert updated_post["title"] == updated_data["title"]
    assert updated_post["seeds"] == updated_data["seeds"]
    assert updated_post["leaches"] == updated_data["leaches"]

# Тест удаления поста через API
def test_api_delete_post(db_session, created_post):
    post_id, rutracker_id = created_post
    response = test_client.delete(f"/posts/{post_id}")
    assert response.status_code == 200
    data = response.json()
    
    # Проверяем, что в ответе есть только id
    assert "id" in data  # Проверяем, что id в ответе есть
    assert data["id"] == post_id
    
    # Убедимся, что пост был удален из базы
    post_in_db = db_session.execute(
        text("""SELECT * FROM public.rutracker_posts WHERE id = :post_id"""),
        {"post_id": post_id}
    ).fetchone()
    assert post_in_db is None

