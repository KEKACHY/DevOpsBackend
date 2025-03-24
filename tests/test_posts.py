import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DevOpsBackend.app.config import Config
from DevOpsBackend.app.models import Base, get_all_posts, get_post_by_id, update_post, delete_post
from DevOpsBackend..app import app
from fastapi.testclient import TestClient
import os

# Устанавливаем конфигурацию для тестов
os.environ["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_TEST_DATABASE_URI
os.environ["SECRET_KEY"] = Config.SECRET_KEY

# Настроим базу данных для тестов
DATABASE_URL = os.getenv("SQLALCHEMY_TEST_DATABASE_URI")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем таблицы в тестовой базе данных
Base.metadata.create_all(bind=engine)

# Настроим тестовый клиент FastAPI
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client

# Фикстура для работы с сессией базы данных
@pytest.fixture(scope="module")
def db_session():
    # Копируем данные из основной базы в тестовую (например, с помощью SQL)
    # Здесь вам нужно будет выполнить миграцию данных в тестовую БД перед началом тестов
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# Тесты
def test_get_all_posts(client, db_session):
    # Добавляем тестовые данные в тестовую базу
    db_session.execute("INSERT INTO rutracker_posts (rutracker_id, link, title, seeds, leaches, size) VALUES ('test_id', 'http://example.com', 'Test Post', 10, 5, '100MB')")
    db_session.commit()

    response = client.get("/posts/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_get_post_by_id(client, db_session):
    # Добавляем тестовые данные
    db_session.execute("INSERT INTO rutracker_posts (rutracker_id, link, title, seeds, leaches, size) VALUES ('test_id', 'http://example.com', 'Test Post', 10, 5, '100MB')")
    db_session.commit()

    response = client.get("/posts/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Post"

def test_update_post(client, db_session):
    # Добавляем тестовые данные
    db_session.execute("INSERT INTO rutracker_posts (rutracker_id, link, title, seeds, leaches, size) VALUES ('test_id', 'http://example.com', 'Test Post', 10, 5, '100MB')")
    db_session.commit()

    response = client.put("/posts/1", json={
        "rutracker_id": "updated_id",
        "link": "http://example.com/updated",
        "title": "Updated Post",
        "seeds": 20,
        "leaches": 10,
        "size": "200MB"
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Post"

def test_delete_post(client, db_session):
    # Добавляем тестовые данные
    db_session.execute("INSERT INTO rutracker_posts (rutracker_id, link, title, seeds, leaches, size) VALUES ('test_id', 'http://example.com', 'Test Post', 10, 5, '100MB')")
    db_session.commit()

    response = client.delete("/posts/1")
    assert response.status_code == 200

    # Проверяем, что пост был удален
    response = client.get("/posts/1")
    assert response.status_code == 404
