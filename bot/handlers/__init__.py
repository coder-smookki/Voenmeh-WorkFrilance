from bot.handlers.main_menu import router as menu_router
from bot.handlers.suggestion.suggestion_user import suggestion_user_router
from bot.handlers.suggestion.suggestion_moder import moderation_router
from bot.handlers.order.order_user import order_user_router
from bot.handlers.go_to_menu_command import go_to_menu_router
from bot.handlers.order.order_executor import order_executor_router

__all__ = [
    'menu_router', 'suggestion_user_router', 
    'moderation_router', 'order_user_router', 'go_to_menu_router',
    'order_executor_router'
    ]