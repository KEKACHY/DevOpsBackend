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
def add_post(db: Session, rutracker_id: str, link: str, title: str, seeds: int, leaches: int, size: str):
    db.execute(
        text("CALL add_posts(:rutracker_id, :link, :title, :seeds, :leaches, :size)"),
        {
            "rutracker_id": rutracker_id,
            "link": link,
            "title": title,
            "seeds": seeds,
            "leaches": leaches,
            "size": size
        }
    )
    db.commit()
    return get_post_id_by_rutracker_id(db, rutracker_id)

# Функция для обновления поста
def update_post(db: Session, post_id: int, rutracker_id: str, link: str, title: str, seeds: int, leaches: int, size: str):
    db.execute(
        text("CALL update_post(:post_id, :rutracker_id, :link, :title, :seeds, :leaches, :size)"),
        {
            "post_id": post_id,
            "rutracker_id": rutracker_id,
            "link": link,
            "title": title,
            "seeds": seeds,
            "leaches": leaches,
            "size": size
        }
    )
    db.commit()

# Функция для удаления поста
def delete_post(db: Session, post_id: int):
    db.execute(text("CALL delete_post(:post_id)"), {"post_id": post_id})
    db.commit()
