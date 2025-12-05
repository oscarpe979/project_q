from functools import lru_cache
from fastapi import Depends
from .config import Settings
from backend.app.services.genai_parser import GenAIParser

@lru_cache()
def get_settings():
    return Settings()

def get_genai_parser(settings: Settings = Depends(get_settings)) -> GenAIParser:
    return GenAIParser(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
