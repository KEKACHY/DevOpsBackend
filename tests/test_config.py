import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestConfig:
    SQLALCHEMY_DATABASE_TEST_URI = os.environ["SQLALCHEMY_DATABASE_TEST_URI"]
    SECRET_KEY = os.environ["SECRET_KEY"]

# Инициализация подключения
engine = create_engine(TestConfig.SQLALCHEMY_DATABASE_TEST_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)