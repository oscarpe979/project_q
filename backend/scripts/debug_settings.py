import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from backend.app.core.config import settings
    print(f"DEBUG: DATABASE_URL={settings.DATABASE_URL}")
    print(f"DEBUG: GEMINI_API_KEY_LENGTH={len(settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else 0}")
    print(f"DEBUG: Env File Path={settings.Config.env_file}")
    print(f"DEBUG: Env File Exists={os.path.exists(settings.Config.env_file)}")
except Exception as e:
    print(f"ERROR: {e}")
