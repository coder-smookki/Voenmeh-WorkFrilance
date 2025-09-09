from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_suggestion_files_keyboard(submission_id: str): 
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton( text='🚫 Без файлов', callback_data=f'sub_nofiles:{submission_id}')],
            [InlineKeyboardButton(text='✏️ Редактировать описание', callback_data='edit_sub_description')],
            [InlineKeyboardButton(text='⬅️ В главное меню', callback_data='go_to_menu')]
        ]
    )
    return keyboard

def get_suggestion_done_keyboard(submission_id: str):
    keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='✅Готово', callback_data=f'sub_done:{submission_id}')]
    ]
    )
    return keyboard

def get_order_files_keyboard(order_id: str): 
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton( text='🚫 Без файлов', callback_data=f'order_nofiles:{order_id}')],
            [InlineKeyboardButton(text='✏️ Редактировать описание', callback_data='edit_order_description')],
            [InlineKeyboardButton(text='⬅️ В главное меню', callback_data='go_to_menu')]
        ]
    )
    return keyboard

def get_order_done_keyboard(order_id: str):
    keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='✅ Готово', callback_data=f'order_done:{order_id}')]
    ]
    )
    return keyboard