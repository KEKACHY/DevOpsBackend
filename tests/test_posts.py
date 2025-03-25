import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

# Настройка тестовой базы данных
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

test_client = TestClient(app)

@pytest.fixture
def db_session():
    # Открываем сессию для каждого теста
    db = SessionLocal()
    # Начинаем транзакцию
    db.begin()
    yield db
    # Откатываем транзакцию после завершения теста
    db.rollback()
    db.close()

# Тест получения всех постов через API
def test_api_get_all_posts(db_session):
    # Сначала создаем несколько постов в тестовой базе
    db_session.execute(
        text("""
        SELECT public.create_posts('test123', 'http://example.com', 'Test Post', 10, 5, '700MB');
        """)
    )
    db_session.commit()
    
    response = test_client.get("/posts/")
    assert response.status_code == 200
    posts = response.json()
    assert isinstance(posts, list)
    assert len(posts) > 0  # Убедимся, что список не пустой

# Тест создания нового поста через API
def test_api_create_post(db_session):
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
    # Проверим, что пост действительно был создан в базе
    post_in_db = db_session.execute(
        text("""
        SELECT * FROM public.rutracker_posts WHERE rutracker_id = :rutracker_id
        """), 
        {"rutracker_id": new_post["rutracker_id"]}
    ).fetchone()
    assert post_in_db is not None

# Тест получения поста по ID через API
def test_api_get_post_by_id(db_session):
    # Сначала создаем пост в базе данных для теста
    post_id = db_session.execute(
        text("""
        SELECT public.create_posts('test123', 'http://example.com', 'Test Post', 10, 5, '700MB');
        """)
    ).fetchone()[0]
    db_session.commit()
    
    response = test_client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    post_data = response.json()
    assert post_data["id"] == post_id
    assert "rutracker_id" in post_data

# Тест обновления поста через API
def test_api_update_post(db_session):
    # Сначала создаем пост в базе для теста
    post_id = db_session.execute(
        text("""
        SELECT public.create_posts('test123', 'http://example.com', 'Test Post', 10, 5, '700MB');
        """)
    ).fetchone()[0]
    db_session.commit()
    
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
def test_api_delete_post(db_session):
    # Сначала создаем пост в базе для теста
    post_id = db_session.execute(
        text("""
        SELECT public.create_posts('test123', 'http://example.com', 'Test Post', 10, 5, '700MB');
        """)
    ).fetchone()[0]
    db_session.commit()

    response = test_client.delete(f"/posts/{post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post_id
    
    # Убедимся, что пост был удален из базы
    post_in_db = db_session.execute(
        text("""
        SELECT * FROM public.rutracker_posts WHERE id = :post_id
        """), 
        {"post_id": post_id}
    ).fetchone()
    assert post_in_db is None
