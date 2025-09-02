from aiogram import Router
from aiogram.filters.command import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


router = Router(name="start/menu")


start_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Перейти в меню", callback_data="go_to_menu")]
    ]
)

@router.message(CommandStart())
async def start_command(message: Message):
    welcome_text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Я ваш помощник. Нажмите на кнопку ниже, чтобы перейти в главное меню."
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Перейти в меню", callback_data="go_to_menu")]
        ]
    )
    
    await message.answer(
        text=welcome_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
