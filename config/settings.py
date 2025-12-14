import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
AI_API_KEY = os.getenv("AI_API_KEY", "")

IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "local")
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY", "")

AI_MODELS = {
    "claude": "claude-sonnet-4-20250514",
    "gemini": "gemini-1.5-flash",
    "groq": "llama-3.3-70b-versatile",  # Быстрая бесплатная модель
    "ollama": "llama3.1"  # Локальная модель
}

AI_MODEL = os.getenv("AI_MODEL", AI_MODELS.get(AI_PROVIDER, "gemini-1.5-flash"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", AI_API_KEY)
CLAUDE_MODEL = "claude-sonnet-4-20250514"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///newsmaker.db")

PLATFORMS = {
    "telegram": {
        "name": "Telegram",
        "max_length": 4096,
        "emoji": True,
        "hashtags": True
    },
    "vk": {
        "name": "ВКонтакте",
        "max_length": 4096,
        "emoji": True,
        "hashtags": True
    },
    "twitter": {
        "name": "Twitter/X",
        "max_length": 280,
        "emoji": True,
        "hashtags": True
    },
    "linkedin": {
        "name": "LinkedIn",
        "max_length": 3000,
        "emoji": False,
        "hashtags": True,
        "formal": True
    },
    "press": {
        "name": "Пресс-релиз",
        "max_length": 1500,
        "emoji": False,
        "hashtags": False,
        "formal": True
    }
}

POSTING_HOURS = {
    "morning": [8, 9, 10],
    "day": [12, 13, 14, 15],
    "evening": [18, 19, 20]
}

DEBUG = os.getenv("DEBUG", "False") == "True"