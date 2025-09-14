import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI"]
    SECRET_KEY = os.environ["SECRET_KEY"]

    # Токен бота и ID чата
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "7987831032:AAEI8FahwKLKUQL5mxrGxkYgWtRIdeVoZ_s")
    CHAT_ID = os.environ.get("CHAT_ID", "-1002940859370")

# Инициализация подключения
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)