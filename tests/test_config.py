# test_config.py
import os

class TestConfig:
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_TEST_DATABASE_URI")
    SQLALCHEMY_TEST_DATABASE_URI = os.getenv("SQLALCHEMY_TEST_DATABASE_URI")
    SECRET_KEY = os.getenv("SECRET_KEY")
