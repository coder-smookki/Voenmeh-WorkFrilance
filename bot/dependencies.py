from typing import AsyncGenerator
from database.repo.requests import RequestsRepo
from database.session import async_session  # Теперь этот импорт будет работать
from sqlalchemy.ext.asyncio import AsyncSession

async def get_repo() -> AsyncGenerator[RequestsRepo, None]:
    async with async_session() as session:  # Вызываем как функцию
        yield RequestsRepo(session)


async def get_db_session() -> AsyncSession:
    """Получение сессии БД для использования в хэндлерах"""
    return async_session()