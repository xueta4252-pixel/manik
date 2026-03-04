import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8755530240:AAH_GHtaRCQ1-yxCQAhzHXM7maPRjLRf458")
ADMIN_ID: int = 1063802362
CHANNEL_USERNAME: str = "@testmanikforbot"
PORTFOLIO_URL: str = "https://t.me/testmanikforbot"

DEFAULT_SLOTS: list[str] = ["10:00", "11:30", "13:00", "14:30", "16:00", "17:30"]

CANCEL_LIMIT_HOURS: int = 2
REMINDER_24H: int = 24
REMINDER_5H: int = 5
MONTH_AHEAD: int = 30

DB_PATH: str = os.getenv("DB_PATH", "mani.db")
