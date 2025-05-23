import os
import json


class BotConfings:
    token: str = os.getenv("BOT_TOKEN")
    recipients_ids: list = json.loads(os.getenv("TELEGRAM_RECIPIENT_IDS"))


BOT_CONFIGS = BotConfings()
