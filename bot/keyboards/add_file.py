from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_files_keyboard(submission_id: str): 
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅Готово', callback_data=f'sub_done:{submission_id}')],
            [InlineKeyboardButton( text='🚫Без файлов', callback_data=f'sub_nofiles:{submission_id}')],
            [InlineKeyboardButton(text='✏️Исправить описание', callback_data='edit')],
            [InlineKeyboardButton(text='❌Отменить', callback_data='go_to_menu')]
        ]
    )
    return keyboard