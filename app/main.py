from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from . import models
from pydantic import BaseModel
from typing import List
from .config import SessionLocal
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Разрешаем все origins (для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все домены
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешаем все заголовки
)

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

class PostDeleteResponse(BaseModel):
    id: int

# Функция для получения сессии БД
def get_db():
    db = SessionLocal()
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

# Маршрут для создания нового поста
@app.post("/posts/", response_model=RutrackerPostResponse, status_code=201)
def create_post(post: RutrackerPostCreate, db: Session = Depends(get_db)):
    post_id = models.create_post(db, **post.dict())
    db.commit() 
    
    if not post_id:
        db.rollback()  # Откатываем в случае ошибки
        raise HTTPException(status_code=500, detail="Failed to create or retrieve post")
    
    created_post = models.get_post_by_id(db, post_id)
    return created_post

# Маршрут для обновления поста
@app.put("/posts/{post_id}", response_model=RutrackerPostResponse)
def update_post(post_id: int, post: RutrackerPostCreate, db: Session = Depends(get_db)):
    models.update_post(db, post_id, **post.dict())
    db.commit() 
    updated_post = models.get_post_by_id(db, post_id)
    return updated_post


# Маршрут для удаления поста
@app.delete("/posts/{post_id}", response_model=PostDeleteResponse)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = models.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    models.delete_post(db, post_id)
    db.commit() 
    
    return {"id": post_id}

