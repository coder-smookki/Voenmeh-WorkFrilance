from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_support_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📨 Написать в поддержку", callback_data="write_to_support")],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="go_to_menu")]
        ]
    )
    return keyboard  