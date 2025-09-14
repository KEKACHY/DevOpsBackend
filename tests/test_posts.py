# tests/test_posts.py
import pytest
import uuid
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app, get_db
from app import models
import requests

test_client = TestClient(app)


# ---------------------------
# Фейковая "сессия" БД — минимально реализована
# ---------------------------
class DummyExecuteResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def scalar(self):
        # Для get_post_id_by_rutracker_id
        return self._rows[0] if self._rows else None


class DummyDB:
    def __init__(self):
        self.executed = []

    def commit(self):
        return None

    def refresh(self, obj):
        return None

    def delete(self, obj):
        return None

    def execute(self, stmt, params=None):
        self.executed.append((stmt, params))
        sql = str(stmt)
        if "get_all_posts()" in sql:
            return DummyExecuteResult([{"id": 1, "title": "Post1"}])
        if "get_post_by_id" in sql:
            return DummyExecuteResult([{"id": params["post_id"], "title": "Post1"}])
        if "rutracker_posts" in sql:
            return DummyExecuteResult([42])
        if "create_posts" in sql:
            return DummyExecuteResult([99])  # ID нового поста
        return DummyExecuteResult()

@pytest.fixture
def db():
    return DummyDB()

# ---------------------------
# Фикстура: оверрайдим get_db на DummyDB
# ---------------------------
@pytest.fixture(autouse=True)
def override_get_db():
    def _dummy_db():
        yield DummyDB()
    app.dependency_overrides[get_db] = _dummy_db
    yield
    app.dependency_overrides.clear()


# ---------------------------
# Фикстура: шаблон поста
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

    # models.get_post_by_id должен вернуть объект с атрибутами
    monkeypatch.setattr(
        models,
        "get_post_by_id",
        lambda db, pid: SimpleNamespace(**post_data)
    )

    called = {}

    def mock_post(url, data=None, **kwargs):
        called["url"] = url
        called["data"] = data
        class MockResponse:
            status_code = 200
            def raise_for_status(self): pass
        return MockResponse()

    monkeypatch.setattr(requests, "post", mock_post)

    resp = test_client.post(f"/send-post/{post_id}")
    assert resp.status_code == 200
    body = resp.json()
    # В твоём приложении статус — "ok"
    assert body.get("status") == "ok"

    # Убедимся, что requests.post был вызван корректно
    assert "url" in called and isinstance(called["url"], str)
    assert "data" in called and isinstance(called["data"], dict)


# ---------------------------
# Тест: получить все посты
# ---------------------------
def test_api_get_all_posts(monkeypatch, created_post):
    post_id, _, post_data = created_post

    monkeypatch.setattr(
        models,
        "get_all_posts",
        lambda db: [SimpleNamespace(**post_data)]
    )

    resp = test_client.get("/posts/")
    assert resp.status_code == 200
    posts = resp.json()
    assert isinstance(posts, list)
    assert len(posts) == 1
    assert posts[0]["id"] == post_id


# ---------------------------
# Тест: получить пост по id
# ---------------------------
def test_api_get_post_by_id(monkeypatch, created_post):
    post_id, rutracker_id, post_data = created_post

    def mock_get(db, pid):
        assert pid == post_id
        return SimpleNamespace(**post_data)

    monkeypatch.setattr(models, "get_post_by_id", mock_get)

    resp = test_client.get(f"/posts/{post_id}")
    assert resp.status_code == 200
    data = resp.json()
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

    called = {"update": False}

    def mock_update_post(db, pid, rutracker_id, link, title, seeds, leaches, size):
        # Проверяем, что update_post вызывается с правильными аргументами
        assert pid == post_id
        assert isinstance(rutracker_id, str)
        called["update"] = True
        # Возвращаем что-то, но main.py после commit вызывает get_post_by_id,
        # поэтому окончательный ответ будет от get_post_by_id
        return SimpleNamespace(id=pid, **updated_data)

    # Очень важно: mock get_post_by_id, потому что main.py вызывает его после commit
    def mock_get_post_by_id(db, pid):
        assert pid == post_id
        return SimpleNamespace(id=pid, **updated_data)

    monkeypatch.setattr(models, "update_post", mock_update_post)
    monkeypatch.setattr(models, "get_post_by_id", mock_get_post_by_id)

    resp = test_client.put(f"/posts/{post_id}", json=updated_data)
    assert resp.status_code == 200
    resp_body = resp.json()

    # Убедимся, что update действительно вызван (защита от "silent" ошибки)
    assert called["update"] is True

    for k, v in updated_data.items():
        assert resp_body[k] == v


# ---------------------------
# Тест: удаление поста
# ---------------------------
def test_api_delete_post(monkeypatch, created_post):
    post_id, _, _ = created_post

    called = {"deleted": False}

    # main.py вызывает get_post_by_id перед удалением, поэтому мокируем его
    monkeypatch.setattr(models, "get_post_by_id", lambda db, pid: SimpleNamespace(id=pid))

    def mock_delete_post(db, pid):
        assert pid == post_id
        called["deleted"] = True
        return SimpleNamespace(id=pid)

    monkeypatch.setattr(models, "delete_post", mock_delete_post)

    resp = test_client.delete(f"/posts/{post_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == post_id
    assert called["deleted"] is True




# ---------------------------
# ---------------------------
# Тесты для models.py
# ---------------------------
# ---------------------------

class DummyExecuteResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def scalar(self):
        # Для get_post_id_by_rutracker_id
        return self._rows[0] if self._rows else None


# ---------------------------
# Фейковая сессия
# ---------------------------


# ---------------------------
# Фикстура для DB
# ---------------------------
@pytest.fixture
def db():
    return DummyDB()


# ---------------------------
# Тест: get_all_posts
# ---------------------------
def test_get_all_posts(db):
    posts = models.get_all_posts(db)
    assert isinstance(posts, list)
    assert posts[0]["id"] == 1
    assert "get_all_posts()" in str(db.executed[0][0])


# ---------------------------
# Тест: get_post_by_id
# ---------------------------
def test_get_post_by_id(db):
    post = models.get_post_by_id(db, 5)
    assert post["id"] == 5
    stmt, params = db.executed[0]
    assert params["post_id"] == 5


# ---------------------------
# Тест: get_post_id_by_rutracker_id
# ---------------------------
def test_get_post_id_by_rutracker_id(db):
    post_id = models.get_post_id_by_rutracker_id(db, "abc123")
    assert post_id == 42
    stmt, params = db.executed[0]
    assert params["rutracker_id"] == "abc123"


# ---------------------------
# Тест: create_post
# ---------------------------
def test_create_post(db):
    new_id = models.create_post(db, "rut123", "link", "title", 10, 5, "700MB")
    assert new_id == 99
    stmt, params = db.executed[0]
    assert params["title"] == "title"


# ---------------------------
# Тест: update_post
# ---------------------------
def test_update_post(db):
    models.update_post(db, 1, "rut123", "link", "title", 10, 5, "700MB")
    stmt, params = db.executed[0]
    assert params["post_id"] == 1


# ---------------------------
# Тест: delete_post
# ---------------------------
def test_delete_post(db):
    models.delete_post(db, 7)
    stmt, params = db.executed[0]
    assert params["post_id"] == 7