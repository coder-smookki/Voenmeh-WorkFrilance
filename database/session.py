from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from typing import Optional
from database.settings import DBSettings

# Глобальная переменная для sessionmaker
_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None

async def init_session(db_settings: DBSettings) -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    async_engine = create_async_engine(db_settings.url)

    # Проверка подключения к базе данных
    async with async_engine.begin():
        pass

    _sessionmaker = async_sessionmaker(
        bind=async_engine,
        autoflush=False,
        future=True,
        expire_on_commit=False,
    )
    return _sessionmaker

# Функция для получения сессии
async def async_session() -> AsyncSession:
    if _sessionmaker is None:
        raise RuntimeError("Session maker not initialized. Call init_session first.")
    return _sessionmaker()