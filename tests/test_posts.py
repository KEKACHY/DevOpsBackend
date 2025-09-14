import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app import models
import requests 
from types import SimpleNamespace

test_client = TestClient(app)

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
