from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_start_keyboard():
    start_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='💥 Заказать работу', callback_data='create_order')],
            [InlineKeyboardButton(text='🛡 База решений', callback_data='solutions')],
            [InlineKeyboardButton(text='☮️ Отправить работу', callback_data='suggestion')],
            [InlineKeyboardButton(text='⚡️ Поддержка', callback_data='support')],
            [InlineKeyboardButton(text='📋 Мои заказы', callback_data='my_orders')]
        ]
    )
    return start_keyboard
