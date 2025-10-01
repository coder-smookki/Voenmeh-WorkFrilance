from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
import logging
from database.repo.requests import RequestsRepo

logger = logging.getLogger(__name__)


class UserContextMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        session = data.get('session')
        if not session:
            logger.error("❌ Session not found in data")
            return await handler(event, data)
        
        # Создаем репозитории
        repo = RequestsRepo(session)
        data['repo'] = repo
        data['user_repo'] = repo.users
        
        # Извлекаем message или callback_query из event
        if isinstance(event, Update):
            message = event.message
            callback_query = event.callback_query
        elif isinstance(event, Message):
            message = event
            callback_query = None
        elif isinstance(event, CallbackQuery):
            message = None
            callback_query = event
        else:
            logger.warning(f"⚠️ Unknown event type: {type(event)}")
            return await handler(event, data)
        
        # Определяем user_id и chat_id
        if message:
            user_id = message.from_user.id
            chat_id = message.chat.id
            from_user = message.from_user
        elif callback_query:
            user_id = callback_query.from_user.id
            chat_id = callback_query.message.chat.id if callback_query.message else user_id
            from_user = callback_query.from_user
        else:
            return await handler(event, data)
        
        try:
            user = await repo.users.get_or_create(
                user_id=user_id,
                chat_id=chat_id,
                username=getattr(from_user, 'username', None),
                first_name=getattr(from_user, 'first_name', None)
            )
            
            if not user:
                logger.error(f"❌ Failed to create/find user {user_id}")
                return await handler(event, data)
            
            data['user'] = user
            
        except Exception as e:
            logger.error(f"❌ Error in UserContextMiddleware: {e}", exc_info=True)
        
        return await handler(event, data)