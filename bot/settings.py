import os
from pydantic import BaseModel, PostgresDsn  # Или используйте str если предпочитаете

class DatabaseSettings(BaseModel):
    database_url: str  # или PostgresDsn для проверки формата
    # либо отдельные параметры:
    # host: str
    # port: int
    # name: str
    # user: str
    # password: str

class BotSettings(BaseModel):
    token: str
    moder_chat_id: str = os.environ['MODERATOR_CHAT_ID']
    support_chat_id: str = os.environ['SUPPORT_CHAT_ID']
    order_chat_id: str = os.environ['ORDER_CHAT_ID']

class RedisSettings(BaseModel):
    redis_url: str

class Settings(BaseModel):
    bot_settings: BotSettings
    redis_settings: RedisSettings
    database_settings: DatabaseSettings  # Добавьте эту строку

def get_settings() -> Settings:
    return Settings(
        bot_settings=BotSettings(
            token=os.environ["TOKEN"],
            moder_chat_id=os.environ['MODERATOR_CHAT_ID'],
            support_chat_id=os.environ['SUPPORT_CHAT_ID'],
            order_chat_id=os.environ['ORDER_CHAT_ID'],
        ),
        redis_settings=RedisSettings(
            redis_url=os.environ["REDIS_URL"],
        ),
        database_settings=DatabaseSettings(
            database_url=os.environ["DATABASE_URL"]  # Добавьте эту строку
        )
    )