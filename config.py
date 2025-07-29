import os
from dotenv import load_dotenv


load_dotenv()

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST"),
}

ADMIN_ID = int(os.getenv('ADMIN_ID'))

BOT_TOKEN = os.getenv("BOT_TOKEN")

MONGO_API_TOKEN = os.getenv("MONGO_API_TOKEN")