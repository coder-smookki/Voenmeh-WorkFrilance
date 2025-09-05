import asyncio

from aiogram import Bot, Dispatcher

from bot.settings import TOKEN
from bot.handlers import menu_router
from bot.handlers import main_menu
from bot.handlers import suggestion_user_router
from bot.handlers import moderation_router
from bot.handlers.help import help_router


def include_routers(dp: Dispatcher) -> None:
    dp.include_router(menu_router)
    dp.include_router(suggestion_user_router)
    dp.include_router(moderation_router)
    dp.include_router(help_router)

def create_bot(token) -> Bot:
    return Bot(token=token)


async def main():
    
    bot = create_bot(TOKEN)
    dp = Dispatcher()

    include_routers(dp)

    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())