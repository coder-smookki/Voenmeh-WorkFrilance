from logging import Logger
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message, Update


class LoggingMiddleware(BaseMiddleware):
    def __init__(
        self,
        logger: Logger
    ) -> None:
        self.logger = logger
        
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event.event, CallbackQuery):
            callback: CallbackQuery = event.event
            self.logger.info(
                "Received callback, id: %s, user_id: %s, data: %s", 
                callback.id, 
                callback.from_user.id,
                callback.data
            )
        elif isinstance(event.event, Message):
            message: Message = event.event
            self.logger.info(
                "Received message, id: %s, user_id: %s, data: %s", 
                message.message_id, 
                message.from_user.id,
                message.text
            )
        try:
            result = await handler(event, data)
            return result
        except Exception as exc:
            if isinstance(event.event, CallbackQuery):
                callback: CallbackQuery = event.event
                self.logger.error(
                    "Exception in callback, id: %s, user_id: %s, data: %s, exception: %s", 
                    callback.id, 
                    callback.from_user.id,
                    callback.data,
                    str(exc)
                )
            elif isinstance(event.event, Message):
                message: Message = event.event
                self.logger.error(
                    "Exception in message, id: %s, user_id: %s, text: %s, exception: %s", 
                    message.message_id, 
                    message.from_user.id,
                    message.text,
                    str(exc)
                )