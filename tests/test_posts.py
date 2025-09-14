import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base  # Твои модели SQLAlchemy

# Создаём SQLite in-memory
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
SessionTesting = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

test_client = TestClient(app)

# Fixture для сессии БД
@pytest.fixture
def db_session():
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()

# Fixture для тестового поста
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

# Тест отправки поста
def test_send_post(monkeypatch, db_session, created_post):
    post_id, rutracker_id, post_data = created_post

    # Мок функции get_post_by_id
    def mock_get_post_by_id(db, post_id):
        return post_data

    monkeypatch.setattr("app.models.get_post_by_id", mock_get_post_by_id)

    # Мок requests.post
    def mock_post(url, data=None, **kwargs):
        class MockResponse:
            status_code = 200
            def raise_for_status(self): pass
        return MockResponse()

    monkeypatch.setattr("requests.post", mock_post)

    response = test_client.post(f"/send-post/{post_id}")
    assert response.status_code == 200

    
#     # Получаем ID созданного поста без коммита
#     post_id = db_session.execute(
#         text("""SELECT id FROM public.rutracker_posts WHERE rutracker_id = :rutracker_id"""),
#         {"rutracker_id": new_post["rutracker_id"]}
#     ).fetchone()[0]
    
#     return post_id, new_post["rutracker_id"]

# # Тест получения всех постов через API
# def test_api_get_all_posts(db_session, created_post):
#     response = test_client.get("/posts/")
#     assert response.status_code == 200
#     posts = response.json()
#     assert isinstance(posts, list)
#     assert len(posts) > 0

# # Тест получения поста по ID через API
# def test_api_get_post_by_id(db_session, created_post):
#     post_id, rutracker_id = created_post
#     response = test_client.get(f"/posts/{post_id}")
#     assert response.status_code == 200
#     post_data = response.json()
#     assert post_data["id"] == post_id
#     assert post_data["rutracker_id"] == rutracker_id

# # Тест обновления поста через API
# def test_api_update_post(db_session, created_post):
#     post_id, rutracker_id = created_post
#     updated_data = {
#         "rutracker_id": f"updated-{uuid.uuid4()}",  # Генерация уникального ID
#         "link": "http://example.com/updated",
#         "title": "Updated Post",
#         "seeds": 20,
#         "leaches": 10,
#         "size": "1GB"
#     }
#     response = test_client.put(f"/posts/{post_id}", json=updated_data)
#     assert response.status_code == 200
#     updated_post = response.json()
#     assert updated_post["rutracker_id"] == updated_data["rutracker_id"]
#     assert updated_post["title"] == updated_data["title"]
#     assert updated_post["seeds"] == updated_data["seeds"]
#     assert updated_post["leaches"] == updated_data["leaches"]

# # Тест удаления поста через API
# def test_api_delete_post(db_session, created_post):
#     post_id, rutracker_id = created_post
#     response = test_client.delete(f"/posts/{post_id}")
#     assert response.status_code == 200
#     data = response.json()
    
#     # Проверяем, что в ответе есть только id
#     assert "id" in data  # Проверяем, что id в ответе есть
#     assert data["id"] == post_id
    
#     # Убедимся, что пост был удален из базы
#     post_in_db = db_session.execute(
#         text("""SELECT * FROM public.rutracker_posts WHERE id = :post_id"""),
#         {"post_id": post_id}
#     ).fetchone()
#     assert post_in_db is None

