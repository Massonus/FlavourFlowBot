from dotenv import load_dotenv
import os

# download secrets from .env file that should be in the main directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'dev.env')
load_dotenv(dotenv_path=dotenv_path)

APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
TG_TOKEN = os.getenv("TG_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = os.getenv("ADMIN_ID")
ADMIN2_ID = os.getenv("ADMIN2_ID")
INITIALIZE_ENGINE = os.getenv("INITIALIZE_ENGINE")
