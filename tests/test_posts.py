import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app import models
import requests 
from types import SimpleNamespace

test_client = TestClient(app)

# ---------------------------
# База данных
# ---------------------------
@pytest.fixture
def db_session():
    from app.config import SessionLocal
    db = SessionLocal()
    db.begin()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

# ---------------------------
# Создание поста
# ---------------------------
@pytest.fixture
def created_post():
    post_id = 1
    rutracker_id = str(uuid.uuid4())
    post_data = {
        "id": post_id,
        "rutracker_id": rutracker_id,
        "link": "http://example.com",
        "title": "Test Post",
        "seeds": 10,
        "leaches": 5,
        "size": "700MB"
    }
    return post_id, rutracker_id, post_data

# ---------------------------
# Тест отправки сообщения
# ---------------------------
def test_send_post(monkeypatch, db_session, created_post):
    post_id, rutracker_id, post_data = created_post

    def mock_get_post_by_id(db, post_id):
        return SimpleNamespace(**post_data)  

    monkeypatch.setattr(models, "get_post_by_id", mock_get_post_by_id)

    def mock_post(url, data=None, **kwargs):
        class MockResponse:
            status_code = 200
            def raise_for_status(self): pass
        return MockResponse()

    import requests
    monkeypatch.setattr(requests, "post", mock_post)

    response = test_client.post(f"/send-post/{post_id}")
    assert response.status_code == 200

# ---------------------------
# Тест получения всех постов
# ---------------------------
def test_api_get_all_posts(monkeypatch, created_post):
    post_id, rutracker_id, post_data = created_post

    # Мокаем get_all_posts
    def mock_get_all_posts(db):
        return [SimpleNamespace(**post_data)]

    monkeypatch.setattr(models, "get_all_posts", mock_get_all_posts)

    response = test_client.get("/posts/")
    assert response.status_code == 200
    posts = response.json()
    assert isinstance(posts, list)
    assert len(posts) == 1
    assert posts[0]["id"] == post_id

# ---------------------------
# Тест получения поста по ID
# ---------------------------
def test_api_get_post_by_id(monkeypatch, created_post):
    post_id, rutracker_id, post_data = created_post

    def mock_get_post_by_id(db, pid):
        assert pid == post_id
        return SimpleNamespace(**post_data)

    monkeypatch.setattr(models, "get_post_by_id", mock_get_post_by_id)

    response = test_client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post_id
    assert data["rutracker_id"] == rutracker_id

# ---------------------------
# Тест обновления поста
# ---------------------------
def test_api_update_post(monkeypatch, created_post):
    post_id, rutracker_id, post_data = created_post
    updated_data = {
        "rutracker_id": f"updated-{uuid.uuid4()}",
        "link": "http://example.com/updated",
        "title": "Updated Post",
        "seeds": 20,
        "leaches": 10,
        "size": "1GB"
    }

    # Мокаем update_post, чтобы ничего не делал
    def mock_update_post(db, pid, rutracker_id, link, title, seeds, leaches, size):
        assert pid == post_id
        return SimpleNamespace(id=pid, **updated_data)

    monkeypatch.setattr(models, "update_post", mock_update_post)

    response = test_client.put(f"/posts/{post_id}", json=updated_data)
    assert response.status_code == 200
    resp_data = response.json()
    assert resp_data["rutracker_id"] == updated_data["rutracker_id"]
    assert resp_data["title"] == updated_data["title"]
    assert resp_data["seeds"] == updated_data["seeds"]
    assert resp_data["leaches"] == updated_data["leaches"]

# ---------------------------
# Тест удаления поста
# ---------------------------
def test_api_delete_post(monkeypatch, created_post):
    post_id, rutracker_id, post_data = created_post

    # Мокаем delete_post
    def mock_delete_post(db, pid):
        assert pid == post_id
        return SimpleNamespace(id=pid)

    monkeypatch.setattr(models, "delete_post", mock_delete_post)

    response = test_client.delete(f"/posts/{post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post_id
