import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from DevOpsBackend.app.config import Config
from DevOpsBackend.app.models import Base
from DevOpsBackend.app import app
from fastapi.testclient import TestClient
import os
import uuid

# Генерируем уникальное имя для тестовой БД
TEST_DB_NAME = f"test_db_{uuid.uuid4().hex[:8]}"
MASTER_DB_URI = Config.SQLALCHEMY_DATABASE_URI
TEST_DB_URI = Config.SQLALCHEMY_DATABASE_URI.rsplit('/', 1)[0] + f"/{TEST_DB_NAME}"

# ----- Фикстуры для управления тестовой БД -----
@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Создаёт временную БД перед всеми тестами и удаляет после"""
    # Подключаемся к основной БД для создания тестовой
    master_engine = create_engine(MASTER_DB_URI, isolation_level="AUTOCOMMIT")
    with master_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    
    # Настраиваем соединение с тестовой БД
    os.environ["SQLALCHEMY_TEST_DATABASE_URI"] = TEST_DB_URI
    engine = create_engine(TEST_DB_URI)
    Base.metadata.create_all(engine)
    
    yield  # Здесь выполняются все тесты
    
    # Пост-очистка: удаляем тестовую БД
    engine.dispose()
    with master_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE {TEST_DB_NAME}"))
    master_engine.dispose()

@pytest.fixture
def db_session():
    """Изолированная сессия для каждого теста с откатом изменений"""
    engine = create_engine(TEST_DB_URI)
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client():
    """Тестовый клиент FastAPI"""
    with TestClient(app) as client:
        yield client

# ----- Тестовые данные -----
TEST_POST = {
    "rutracker_id": "test_id",
    "link": "http://example.com",
    "title": "Test Post",
    "seeds": 10,
    "leaches": 5,
    "size": "100MB"
}

# ----- Тесты -----
def test_get_all_posts(client, db_session):
    db_session.execute(text("""
        INSERT INTO rutracker_posts 
        (rutracker_id, link, title, seeds, leaches, size) 
        VALUES (:id, :link, :title, :seeds, :leaches, :size)
    """), TEST_POST)
    db_session.commit()

    response = client.get("/posts/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_get_post_by_id(client, db_session):
    db_session.execute(text("""
        INSERT INTO rutracker_posts 
        (rutracker_id, link, title, seeds, leaches, size) 
        VALUES (:id, :link, :title, :seeds, :leaches, :size)
    """), TEST_POST)
    db_session.commit()

    response = client.get("/posts/1")
    assert response.status_code == 200
    assert response.json()["title"] == TEST_POST["title"]

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
