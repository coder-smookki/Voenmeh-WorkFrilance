from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_back_to_menu_keyboard():
    bact_to_menu_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⬅️В главное меню', callback_data='go_to_menu')]
        ]
    )
    return bact_to_menu_keyboard
