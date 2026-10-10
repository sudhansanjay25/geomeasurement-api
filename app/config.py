from pathlib import Path 
import os 

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    DATABASE_URL : str = os.getenv("DATABASE_URL",
    f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}")

    UPLOAD_DIR : Path = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
    MAX_UPLOAD_SIZE : int = int(os.getenv("MAX_UPLOAD_SIZE", 10))
    MAX_UPLOAD_SIZE_MB : int = int(MAX_UPLOAD_SIZE * 1024 * 1024)
    ALLOWED_EXTENSION : set[str] = {".zip", ".kml"}

    DEFAULT_PAGE_SIZE : int = int(os.getenv("DEFAULT_PAGE_SIZE", 50))
    MAX_PAGE_SIZE : int = int(os.getenv("MAX_PAGE_SIZE", 500))
    
settings = Config() 