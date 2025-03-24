from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import Config

# Строка подключения к БД PostgreSQL
SQLALCHEMY_DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI

# Создаем подключение к базе данных
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Создаем сессию для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
