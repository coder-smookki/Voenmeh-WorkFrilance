from bot.handlers.main_menu import router as menu_router
from bot.handlers.suggestion.suggestion_user import suggestion_user_router
from bot.handlers.suggestion.suggestion_moder import moderation_router

__all__ = ['menu_router', 'suggestion_user_router', 'moderation_router']