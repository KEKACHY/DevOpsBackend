# test_config.py

import os

class TestConfig:
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_TEST_DATABASE_URI", "postgresql://postgres:password@localhost/test_db")
    SQLALCHEMY_TEST_DATABASE_URI = os.getenv("SQLALCHEMY_TEST_DATABASE_URI", "postgresql://postgres:password@localhost/test_db")
    SECRET_KEY = os.getenv("SECRET_KEY", "testsecret")
