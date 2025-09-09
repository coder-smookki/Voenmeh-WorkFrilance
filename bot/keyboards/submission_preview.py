from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_submission_preview_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅Отправить на модерацию', callback_data='confirm_submission')],
            [InlineKeyboardButton(text='📎Добавить файлы', callback_data='add_more_files')],
            [InlineKeyboardButton(text='✏️Редактировать описание', callback_data='edit_sub_description')],
            [InlineKeyboardButton(text='⬅️В главное меню', callback_data='go_to_menu')]
        ]
    )
    return keyboard  

def get_cancel_current_action():
    keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отменить редактирование', callback_data='cancel_editing')]
        ])
    return keyboard 

def get_moderator_keyboard(submission_id):
    moderator_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять в базу", callback_data=f"accept_{submission_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{submission_id}")]
        ])
    return moderator_keyboard