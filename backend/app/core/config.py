import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

load_dotenv(BACKEND_DIR / ".env")


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/bidagent")
    upload_dir: str = os.getenv("UPLOAD_DIR", str(PROJECT_ROOT / "backend" / "uploads"))
    data_dir: str = str(PROJECT_ROOT / "data")

    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")


settings = Settings()
