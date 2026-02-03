# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# GENERAL
ENV = os.getenv("FLASK_ENV", "development")
DEBUG = ENV == "development"

# API KEYS
HKGAI_API_KEY = os.getenv("HKGAI_API_KEY")

# Weather API
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Search API
SERPAPI_KEY = os.getenv("GOOGLE_SEARCH_API_KEY") 

GOLD_API_KEY = os.getenv("GOLD_API_KEY")

