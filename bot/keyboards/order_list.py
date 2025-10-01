from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_inform_executor_keyboard(order):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="💬 Ответить исполнителю", 
            callback_data=f"reply_executor:{order.id}"
        )
    ]])
    
    return keyboard

def get_view_order_keyboard(order_id):
    keyboard  =InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"view_order:{order_id}")
    ]])
    return keyboard

def get_order_details_keyboard(order):
    
    keyboard = [
        [InlineKeyboardButton(
            text="💬 Написать исполнителю", 
            callback_data=f"message_executor:{order.id}"
        )],
        [
            InlineKeyboardButton(text="📋 К списку заказов", callback_data="order_list"),
            InlineKeyboardButton(text="🔙 В меню", callback_data="go_to_menu")
        ]
    ]
    return keyboard

def get_order_list_keyboard(orders: list) -> InlineKeyboardMarkup:
    keyboard_buttons = []
    
    for order in orders[:10]:
        short_id = order.id[:8]
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📦 #{short_id}",
                callback_data=f"view_order:{order.id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 В меню", callback_data="go_to_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)