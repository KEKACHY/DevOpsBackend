from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_get_posts():
    response = client.get("/posts/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_post():
    response = client.get("/posts/1")
    assert response.status_code == 200
    assert "id" in response.json()

def test_update_post():
    response = client.put("/posts/1", json={
        "rutracker_id": "new_id", "link": "new_link", "title": "new_title",
        "seeds": 10, "leaches": 5, "size": "1GB"
    })
    assert response.status_code == 200
    assert response.json()["title"] == "new_title"

def test_delete_post():
    response = client.delete("/posts/1")
    assert response.status_code == 200
    assert "id" in response.json()
