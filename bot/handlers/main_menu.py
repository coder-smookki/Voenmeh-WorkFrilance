from aiogram import Router
from aiogram.filters.command import CommandStart 
from aiogram.types import Message
from bot.keyboards.start_keyboard import get_start_keyboard
from bot.utils.consts import WELCOME_TEXT

router = Router(name='start/menu')

@router.message(CommandStart())
async def start_command(message: Message, user):
    
    await message.answer(
        text = WELCOME_TEXT,
        parse_mode = 'HTML',
        reply_markup = get_start_keyboard()
    )
    
