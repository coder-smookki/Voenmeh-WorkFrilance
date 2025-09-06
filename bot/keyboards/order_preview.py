from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_order_preview_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅Отправить заказ', callback_data='confirm_order')],
            [InlineKeyboardButton(text='📎Добавить файлы', callback_data='add_more_files')],
            [InlineKeyboardButton(text='✏️Редактировать описание', callback_data='edit_order_description')],
            [InlineKeyboardButton(text='❌Отменить', callback_data='repeal')]
        ]
    )
    return keyboard  