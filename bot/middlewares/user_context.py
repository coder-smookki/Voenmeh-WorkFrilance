from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from database.repo.user import UserRepo, NotFoundException


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            user = await UserRepo(data["session"]).get(data["event_from_user"].id)
            data.update(user=user)
        except NotFoundException:
            data.update(user=None)
        return await handler(event, data)