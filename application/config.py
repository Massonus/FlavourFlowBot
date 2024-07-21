from dotenv import load_dotenv
import os

# download secrets from .env file that should be in the main directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'dev.env')
load_dotenv(dotenv_path=dotenv_path)

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
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = os.getenv("ADMIN_ID")
ADMIN2_ID = os.getenv("ADMIN2_ID")
INITIALIZE_ENGINE = os.getenv("INITIALIZE_ENGINE")
