from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from . import models
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Модели данных для запросов и ответов
class RutrackerPostCreate(BaseModel):
    rutracker_id: str
    link: str
    title: str
    seeds: int
    leaches: int
    size: str

class RutrackerPostResponse(RutrackerPostCreate):
    id: int

    class Config:
        orm_mode = True

# Функция для получения сессии БД
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Маршрут для получения всех постов
@app.get("/posts/", response_model=List[RutrackerPostResponse])
def get_posts(db: Session = Depends(get_db)):
    posts = models.get_all_posts(db)
    return posts

# Маршрут для получения поста по ID
@app.get("/posts/{post_id}", response_model=RutrackerPostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = models.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# Маршрут для обновления поста
@app.put("/posts/{post_id}", response_model=RutrackerPostResponse)
def update_post(post_id: int, post: RutrackerPostCreate, db: Session = Depends(get_db)):
    models.update_post(db, post_id, **post.dict())
    return {**post.dict(), "id": post_id}

# Маршрут для удаления поста
@app.delete("/posts/{post_id}", response_model=RutrackerPostResponse)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = models.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    models.delete_post(db, post_id)
    return {"id": post_id}
