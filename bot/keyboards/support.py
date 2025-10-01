from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_support_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📨 Написать в поддержку", callback_data="write_to_support")],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="go_to_menu")]
        ]
    )
    return keyboard  

def get_reply_to_support_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для ответа пользователю из чата поддержки."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💬 Ответить пользователю",
            callback_data=f"reply_support:{user_id}"
        )]
    ])