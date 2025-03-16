import os
from pathlib import Path
from dotenv import load_dotenv

# Get the root directory of the project
ROOT_DIR = Path(__file__).parent.parent

# Load environment variables from .env file
load_dotenv(ROOT_DIR / ".env")

# CoinGecko API Configuration
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
if not COINGECKO_API_KEY:
    raise ValueError("COINGECKO_API_KEY environment variable is not set")

# CoinGecko API Base URL
COINGECKO_API_BASE_URL = "https://api.coingecko.com/api/v3"
