import os

from pydantic import BaseModel


TOKEN: str = os.environ["TOKEN"]
# ADMINS_IDS: list[int] = list(map(int, os.environ["ADMINS"].split(",")))
MODERATOR_CHAT_ID: str = os.environ['MODERATOR_CHAT_ID']
SUPPORT_CHAT_ID: str = os.environ['SUPPORT_CHAT_ID']
ORDER_CHAT_ID: str = os.environ['ORDER_CHAT_ID']
# REDIS_URL: str = os.environ["REDIS_URL"]

