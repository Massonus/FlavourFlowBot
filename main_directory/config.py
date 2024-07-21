from dotenv import load_dotenv
import os

# Загрузить переменные окружения из .env файла
load_dotenv()

# Test settings
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
POSTGRES_USERNAME = os.getenv("POSTGRES_USERNAME")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_TEST_PASSWORD = os.getenv("POSTGRES_TEST_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_TEST_HOST = os.getenv("POSTGRES_TEST_HOST")
POSTGRES_TEST_DATABASE = os.getenv("POSTGRES_TEST_DATABASE")
POSTGRES_PRACTICE_DATABASE = os.getenv("POSTGRES_PRACTICE_DATABASE")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")
TG_TOKEN = os.getenv("TG_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN2_ID = int(os.getenv("ADMIN2_ID"))

test_engine = (f"postgresql+psycopg://{POSTGRES_USERNAME}:{POSTGRES_TEST_PASSWORD}@{POSTGRES_TEST_HOST}:"
               f"5432/{POSTGRES_PRACTICE_DATABASE}")

host_engine = f"postgresql+psycopg://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DATABASE}"
