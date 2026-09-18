from pathlib import Path
import os
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')
INDEX_PATH = Path(os.getenv('MEDIA_INDEX_PATH') or str(ROOT / 'backend/data/private/media_index.json'))
CORS_ORIGINS = [v.strip() for v in os.getenv('CORS_ORIGINS', 'http://127.0.0.1:8765,http://localhost:8765').split(',') if v.strip()]
