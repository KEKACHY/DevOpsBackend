import pytest
import uuid
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app, get_db
from app import models
import requests

test_client = TestClient(app)

class DummyDB:
    def commit(self): return None
    def refresh(self, obj): return None
    def delete(self, obj): return None
    def execute(self, *args, **kwargs): return None

# ---------------------------
# Фикстура для мокнутой БД
# ---------------------------
@pytest.fixture(autouse=True)
def override_get_db():
    """Подменяем зависимость get_db на фейковую сессию"""
    def dummy_db():
        yield DummyDB()
    app.dependency_overrides[get_db] = dummy_db
    yield
    app.dependency_overrides.clear()


# ---------------------------
# Фикстура для тестового поста
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
        "size": "700MB",
    }
    return post_id, rutracker_id, post_data


# ---------------------------
# Тест: отправка поста в Telegram
# ---------------------------
def test_send_post(monkeypatch, created_post):
    post_id, _, post_data = created_post

    # Мокаем get_post_by_id
    monkeypatch.setattr(
        models,
        "get_post_by_id",
        lambda db, pid: SimpleNamespace(**post_data),
    )

    called = {}

    # Мокаем requests.post
    def mock_post(url, data=None, **kwargs):
        called["url"] = url
        called["data"] = data
        class MockResponse:
            status_code = 200
            def raise_for_status(self): pass
        return MockResponse()

    monkeypatch.setattr(requests, "post", mock_post)

    response = test_client.post(f"/send-post/{post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

    # Проверяем, что requests.post действительно вызвался
    assert "url" in called
    assert "data" in called
    assert isinstance(called["data"], dict)


# ---------------------------
# Тест: получение всех постов
# ---------------------------
def test_api_get_all_posts(monkeypatch, created_post):
    post_id, _, post_data = created_post

    monkeypatch.setattr(
        models,
        "get_all_posts",
        lambda db: [SimpleNamespace(**post_data)],
    )

    response = test_client.get("/posts/")
    assert response.status_code == 200
    posts = response.json()
    assert isinstance(posts, list)
    assert len(posts) == 1
    assert posts[0]["id"] == post_id


# ---------------------------
# Тест: получение поста по ID
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
# Тест: обновление поста
# ---------------------------
def test_api_update_post(monkeypatch, created_post):
    post_id, _, _ = created_post
    updated_data = {
        "rutracker_id": f"updated-{uuid.uuid4()}",
        "link": "http://example.com/updated",
        "title": "Updated Post",
        "seeds": 20,
        "leaches": 10,
        "size": "1GB",
    }

    def mock_update_post(db, pid, rutracker_id, link, title, seeds, leaches, size):
        assert pid == post_id
        return SimpleNamespace(id=pid, **updated_data)

    monkeypatch.setattr(models, "update_post", mock_update_post)

    response = test_client.put(f"/posts/{post_id}", json=updated_data)
    assert response.status_code == 200
    resp_data = response.json()
    for key, value in updated_data.items():
        assert resp_data[key] == value


# ---------------------------
# Тест: удаление поста
# ---------------------------
def test_api_delete_post(monkeypatch, created_post):
    post_id, _, _ = created_post

    def mock_delete_post(db, pid):
        assert pid == post_id
        return SimpleNamespace(id=pid)

    monkeypatch.setattr(models, "delete_post", mock_delete_post)

    response = test_client.delete(f"/posts/{post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post_id
