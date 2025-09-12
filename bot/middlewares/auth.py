from typing import Callable, Dict, Any, Awaitable, cast

from aiogram import BaseMiddleware, Bot, Router
from aiogram.types import TelegramObject, Chat, Message
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove

from database.models.user import User
from bot.utils.consts import BotMenu, AuthActionText


class AuthMiddleware(BaseMiddleware):
    """ Зависим от UserContextMiddleware
    Проверяет юзера на авторизацию
    """
    def __init__(self, exceptions_router: list[str]):
        self.exceptions_router = exceptions_router
        super().__init__()


    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        bot: Bot = data["bot"]
        user: User | None = data.get("user")
        event_chat: Chat | None = data.get("event_chat")
        event_router: Router | None = data.get("event_router")

        if user is not None:
            return await handler(event, data)
        
        if event_router is not None and \
        event_router.name in self.exceptions_router:
            return await handler(event, data)
        
        if isinstance(event, Message):
            message = cast(Message, event)
            if await Command(BotMenu.START)(message, bot):
                return await handler(event, data)
            
        await bot.send_message(
            chat_id=event_chat.id, 
            text=AuthActionText.NOT_AUTH,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )