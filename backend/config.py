import os
from datetime import timedelta
from pathlib import Path

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")

env_path = Path(__file__).resolve().parent / '.env'
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, sep, value = line.partition('=')
        if sep:
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret2024')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'doc_chatbot_jwt_secret_key_32bytes!')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    DB_PATH = os.path.join(os.path.dirname(__file__), 'chatbot.db')