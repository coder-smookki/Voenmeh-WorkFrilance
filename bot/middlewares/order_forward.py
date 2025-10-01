from aiogram import BaseMiddleware
from bot.settings import get_settings
import logging
from bot.keyboards.order_list import get_inform_executor_keyboard

logger = logging.getLogger(__name__)

settings = get_settings()
ORDER_CHAT_ID = int(settings.bot_settings.order_chat_id)

class OrderForwardMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        # Извлекаем сообщение из Update
        message = event.message or (event.callback_query and event.callback_query.message)
        
        if not message:
            return await handler(event, data)
        
        # Быстрые проверки для пропуска обработки
        if (message.chat.id != ORDER_CHAT_ID or
            (message.from_user and message.from_user.id == message.bot.id) or
            (message.text and message.text.startswith('/')) or
            not hasattr(message, 'message_thread_id') or
            not message.message_thread_id or
            hasattr(message, 'forum_topic_created') and message.forum_topic_created or
            hasattr(message, 'forum_topic_edited') and message.forum_topic_edited):
            return await handler(event, data)
        
        # Получаем репозитории
        order_repo = data.get("order_repo")
        user_repo = data.get("user_repo")
        
        if not order_repo or not user_repo:
            logger.error("❌ Required repositories not found in data")
            return await handler(event, data)
        
        try:
            # Ищем заказ по thread_id
            order = await order_repo.get_order_by_thread_id(message.message_thread_id)
            
            if not order:
                logger.warning(f"⚠️ Order not found for thread_id: {message.message_thread_id}")
                return await handler(event, data)
            
            # Находим пользователя
            user = await user_repo.get_by_id(order.user_id)
            if not user:
                logger.error(f"❌ User {order.user_id} not found")
                return await handler(event, data)
            
            # Формируем сообщение для пересылки
            message_text = (
                f"💬 Сообщение от исполнителя по заказу #{order.id[:8]}:\n\n"
                f"{message.text or message.caption or '📎 Вложение'}"
            )
            reply_keyboard = get_inform_executor_keyboard(order)
            
            # Пересылаем сообщение в зависимости от типа контента
            try:
                send_params = {
                    "chat_id": user.user_id,
                    "caption": message_text if message.photo or message.video or message.document or message.audio else None,
                    "text": message_text if not (message.photo or message.video or message.document or message.audio) else None,
                    "reply_markup": reply_keyboard
                }
                
                if message.photo:
                    await message.bot.send_photo(photo=message.photo[-1].file_id, **{k: v for k, v in send_params.items() if v is not None and k != 'text'})
                elif message.video:
                    await message.bot.send_video(video=message.video.file_id, **{k: v for k, v in send_params.items() if v is not None and k != 'text'})
                elif message.document:
                    await message.bot.send_document(document=message.document.file_id, **{k: v for k, v in send_params.items() if v is not None and k != 'text'})
                elif message.audio:
                    await message.bot.send_audio(audio=message.audio.file_id, **{k: v for k, v in send_params.items() if v is not None and k != 'text'})
                else:
                    await message.bot.send_message(**{k: v for k, v in send_params.items() if v is not None and k != 'caption'})
                    
            except Exception as e:
                logger.error(f"❌ Failed to send message to user {user.user_id}: {e}")
                if "bot was blocked" in str(e).lower():
                    await message.reply("❌ Пользователь заблокировал бота")
            
        except Exception as e:
            logger.error(f"❌ Error in order forwarding: {e}", exc_info=True)
        
        return await handler(event, data)