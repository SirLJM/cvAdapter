from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

CV_APP_DIR = Path(r"C:\WORKSPACE\github.com\CV")
CV_CONTENT_DIR = CV_APP_DIR / "static"
CV_APP_URL = "http://localhost:8000"

CV_VERSIONS = ["it", "pm", "ba", "general"]
CV_LANGUAGES = ["en", "pl"]

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "history.db"

ADAPTER_PORT = 8080
