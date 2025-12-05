import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from backend.app.core.config import settings
    print("✅ Settings loaded successfully")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
    
    from backend.app.core.dependencies import get_genai_parser
    parser = get_genai_parser(settings)
    print("✅ GenAIParser initialized successfully")
    
except Exception as e:
    print(f"❌ Verification failed: {e}")
    sys.exit(1)
