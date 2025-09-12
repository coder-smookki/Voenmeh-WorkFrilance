from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.settings import DBSettings


async def init_session(db_settings: DBSettings) -> async_sessionmaker[AsyncSession]:
    async_engine = create_async_engine(db_settings.url)

    # Проверка подключения к базе данных
    async with async_engine.begin():
        pass

    return async_sessionmaker(
        bind=async_engine,
        autoflush=False,
        future=True,
        expire_on_commit=False,
    )