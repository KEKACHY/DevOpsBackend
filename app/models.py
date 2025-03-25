from sqlalchemy.orm import Session
from sqlalchemy import text
from .config import SessionLocal

# Получаем сессию для работы с БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для получения всех постов
def get_all_posts(db: Session):
    result = db.execute(text("SELECT * FROM get_all_posts()"))
    posts = result.fetchall()
    return posts

# Функция для получения поста по ID
def get_post_by_id(db: Session, post_id: int):
    result = db.execute(text("SELECT * FROM get_post_by_id(:post_id)"), {"post_id": post_id})
    post = result.fetchone()
    return post

# Функция для получения ID по RutrackerID
def get_post_id_by_rutracker_id(db: Session, rutracker_id: str):
    result = db.execute(
        text("SELECT id FROM rutracker_posts WHERE rutracker_id = :rutracker_id"),
        {"rutracker_id": rutracker_id}
    )
    return result.scalar()

# Функция для добавления поста
def create_post(db, rutracker_id, link, title, seeds, leaches, size):
    result = db.execute(
        text("SELECT create_posts(:rutracker_id, :link, :title, :seeds, :leaches, :size)"),
        {"rutracker_id": rutracker_id, "link": link, "title": title, 
         "seeds": seeds, "leaches": leaches, "size": size}
    )
    return result.fetchone()[0] 

# Функция для обновления поста
def update_post(db, post_id, rutracker_id, link, title, seeds, leaches, size):
    db.execute(
        text("SELECT update_post(:post_id, :rutracker_id, :link, :title, :seeds, :leaches, :size)"),
        {"post_id": post_id, "rutracker_id": rutracker_id, "link": link,
         "title": title, "seeds": seeds, "leaches": leaches, "size": size}
    )

# Функция для удаления поста
def delete_post(db: Session, post_id: int):
    db.execute(
        text("SELECT delete_post(:post_id)"),
        {"post_id": post_id}
    )
