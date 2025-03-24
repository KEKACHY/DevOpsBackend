import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TEST_DATABASE_URI = os.getenv("SQLALCHEMY_TEST_DATABASE_URI")
    SECRET_KEY = os.getenv("SECRET_KEY")

# Строка подключения к БД PostgreSQL
SQLALCHEMY_DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI

# Создаем подключение к базе данных
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Создаем сессию для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
