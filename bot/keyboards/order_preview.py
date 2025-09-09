from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_order_preview_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Отправить заказ', callback_data='confirm_order')],
            [InlineKeyboardButton(text='📎  Добавить файлы', callback_data='add_more_files')],
            [InlineKeyboardButton(text='✏️ Редактировать описание', callback_data='edit_order_description')],
            [InlineKeyboardButton(text='⬅️ В главное меню', callback_data='go_to_menu')]
        ]
    )
    return keyboard  

def get_cancel_current_action():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='❌ Отменить редактирование', callback_data='cancel_order_editing')]
        ]
    )
    return keyboard 

def get_executor_keyboard(order_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять заказ", callback_data=f"acceptor_{order_id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"rejector_{order_id}")]  
        ]
    )
    return keyboard

def get_complete_order_keyboard(order_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершить заказ", callback_data=f"complete_{order_id}")],
            [InlineKeyboardButton(text="❌ Отклонить заказ", callback_data=f"rejector_{order_id}")]  
        ]
    )
    return keyboard