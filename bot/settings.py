import os

from pydantic import BaseModel


TOKEN: str = os.environ["TOKEN"]
# ADMINS_IDS: list[int] = list(map(int, os.environ["ADMINS"].split(",")))

# REDIS_URL: str = os.environ["REDIS_URL"]

