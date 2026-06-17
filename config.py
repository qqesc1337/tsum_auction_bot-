import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
DEFAULT_AUCTION_DURATION = int(os.getenv("DEFAULT_AUCTION_DURATION", "60"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tsum_auction.db")  # 👈 Railway даст свой URL

MAX_LOT_TITLE_LENGTH = 100
MAX_LOT_DESCRIPTION_LENGTH = 1000
MIN_AUCTION_DURATION = 5
MAX_AUCTION_DURATION = 1440
