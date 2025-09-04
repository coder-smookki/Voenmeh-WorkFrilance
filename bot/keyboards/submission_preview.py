from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_submission_preview_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅Отправить на модерацию', callback_data='confirm_submission')],
            [InlineKeyboardButton(text='📎Добавить файлы', callback_data='add_more_files')],
            [InlineKeyboardButton(text='✏️Редактировать описание', callback_data='edit_submission_text')],
            [InlineKeyboardButton(text='❌Отменить', callback_data='repeal')]
        ]
    )
    return keyboard
