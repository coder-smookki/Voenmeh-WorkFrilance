from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_back_to_menu_keyboard():
    bact_to_menu_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⬅️ В главное меню', callback_data='go_to_menu')]
        ]
    )
    return bact_to_menu_keyboard

def get_cancel_submission_keyboard():
    cancel_submission = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text='❌ Отменить', callback_data='go_to_menu')]
        ]
    )
    return cancel_submission