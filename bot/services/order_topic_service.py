from bot.settings import get_settings
import logging

logger = logging.getLogger(__name__)

class OrderTopicService:
    def __init__(self, bot):
        self.bot = bot
        self.settings = get_settings()
        self.ORDER_CHAT_ID = int(self.settings.bot_settings.order_chat_id)
    
    async def create_order_topic(self, order_id: str, order_description: str, user_message_id: int):
        """Создает топик для заказа и возвращает thread_id ТОЛЬКО при подтверждении исполнителем"""
        try:
            # Создаем топик с отметкой о принятии
            topic = await self.bot.create_forum_topic(
                chat_id=self.ORDER_CHAT_ID,
                name=f"✅ #{order_id[:8]} (активный)"
            )
            
            logger.info(f"✅ Топик создан для принятого заказа {order_id}, thread_id: {topic.message_thread_id}")
            return topic.message_thread_id
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания топика для заказа {order_id}: {e}")
            return None