import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from bot.settings import get_settings
from bot.handlers import menu_router, suggestion_user_router, moderation_router
from bot.handlers.support import help_router
from bot.handlers.order.order_user import order_user_router
from bot.handlers.go_to_menu_command import go_to_menu_router
from bot.handlers.order.order_executor import order_executor_router
from bot.handlers.order.order_list import order_list_router
from bot.middlewares import (
    AuthMiddleware,
    UserContextMiddleware,
    DBSessionMiddleware,
    LoggingMiddleware,
    OrderForwardMiddleware
)
from database.session import init_session
from database.settings import get_db_settings
from bot.utils.logging import setup_logger
from bot.dependencies import get_repo


def include_routers(dp: Dispatcher) -> None:
    dp.include_router(menu_router)
    dp.include_router(suggestion_user_router)
    dp.include_router(moderation_router)
    dp.include_router(help_router)
    dp.include_router(order_user_router)
    dp.include_router(go_to_menu_router)
    dp.include_router(order_executor_router)
    dp.include_router(order_list_router)


def include_middlewares(dp: Dispatcher, session_maker) -> None:
    # Порядок middleware (от внешнего к внутреннему):
    # 1. Логирование
    # 2. Сессия БД
    # 3. Пересылка сообщений из заказов
    # 4. Пользовательский контекст
    # 5. Аутентификация
    
    dp.update.outer_middleware(LoggingMiddleware(logger=setup_logger()))
    dp.update.outer_middleware(DBSessionMiddleware(session_maker))
    dp.update.outer_middleware(OrderForwardMiddleware())
    dp.update.outer_middleware(UserContextMiddleware())
    dp.update.outer_middleware(AuthMiddleware(exceptions_router=["auth"]))


def create_bot(token: str) -> Bot:
    return Bot(token=token)


async def main():
    settings = get_settings()
    db_settings = get_db_settings()

    session_maker = await init_session(db_settings)
    storage = RedisStorage.from_url(settings.redis_settings.redis_url)

    bot = create_bot(settings.bot_settings.token)
    dp = Dispatcher(storage=storage)

    dp["repo"] = get_repo

    include_routers(dp)
    include_middlewares(dp, session_maker)

    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())