from sqlalchemy import select, update
from database.models.user import User
from database.models.order import Order
from database.exceptions import NotFoundException
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class UserRepo:
    def __init__(self, session):
        self.session = session
    
    async def get_or_create(self, user_id: int, chat_id: int, username: str = None, first_name: str = None):
        """Находит пользователя или создает нового"""
        user = await self.get_by_telegram_id(user_id)
        if user:
            return user
        return await self.create_user(user_id, chat_id, username, first_name)
    
    async def get_by_user_id(self, user_id: int):
        """Находит пользователя по telegram user_id"""
        try:
            result = await self.session.execute(
                select(User).where(User.user_id == user_id)
            )
            users = result.scalars().all()
            
            if not users:
                return None
            
            if len(users) == 1:
                return users[0]
            
            logger.warning(f"Найдено {len(users)} дубликатов для user_id {user_id}. Использую последнюю запись.")
            main_user = users[-1]
            
            for old_user in users[:-1]:
                await self.session.delete(old_user)
            
            await self.session.commit()
            return main_user
            
        except Exception as e:
            logger.error(f"Ошибка при поиске пользователя {user_id}: {e}")
            return None
    
    async def create_user(self, user_id: int, chat_id: int, username: str = None, first_name: str = None):
        """Создает нового пользователя"""
        try:
            existing_user = await self.get_by_telegram_id(user_id)
            if existing_user:
                logger.info(f"Пользователь {user_id} уже существует")
                return existing_user
            
            user = User(
                user_id=user_id,
                chat_id=chat_id,
                count_proposed_works=0,
                count_works_ordered=0,
                list_order=""
            )
            
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"Создан новый пользователь: {user_id}")
            return user
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка создания пользователя {user_id}: {e}")
            raise
        
    async def get_by_telegram_id(self, user_id: int):
        """Находит пользователя по telegram user_id"""
        try:
            result = await self.session.execute(
                select(User).where(User.user_id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка при поиске пользователя {user_id}: {e}")
            return None
    
    async def get_by_id(self, id: int):
        """Находит пользователя по primary key"""
        result = await self.session.execute(
            select(User).where(User.id == id)
        )
        return result.scalar_one_or_none()
    
    async def increment_works_count(self, user_id: int) -> None:
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(count_works_ordered=User.count_works_ordered + 1)
        )
        await self.session.execute(stmt)


class OrderRepo:
    def __init__(self, session):
        self.session = session
    
    async def create_order(self, order_id: str, user_id: int, description: str, user_message_id: int = None):
        """Создает новый заказ"""
        try:
            order = Order(
                id=order_id,
                user_id=user_id,
                description=description,
                user_message_id=user_message_id,
                created_at=datetime.now(),
                status='pending'
            )
            self.session.add(order)
            await self.session.commit()
            await self.session.refresh(order)
            return order
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_order_by_thread_id(self, thread_id: int):
        """Находит заказ по ID темы форума"""
        result = await self.session.execute(
            select(Order).where(Order.thread_id == thread_id)
        )
        return result.scalar_one_or_none()
    
    async def get_order_by_id(self, order_id: str):
        """Находит заказ по ID"""
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def update_order_thread(self, order_id: str, thread_id: int, user_message_id: int):
        """Обновляет информацию о топике заказа"""
        order = await self.get_order_by_id(order_id)
        if order:
            order.thread_id = thread_id
            order.user_message_id = user_message_id
            order.status = "active"
            await self.session.commit()
        return order
    
    async def update_order_status(self, order_id: str, status: str):
        """Обновляет статус заказа"""
        order = await self.get_order_by_id(order_id)
        if order:
            order.status = status
            await self.session.commit()
        return order
    
    async def get_user_orders(self, user_id: int):
        """Получает все заказы пользователя"""
        result = await self.session.execute(
            select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def delete_order(self, order_id: str):
        """Удаляет заказ из БД"""
        order = await self.get_order_by_id(order_id)
        if order:
            await self.session.delete(order)
            await self.session.commit()
            logger.info(f"✅ Заказ {order_id} удален из БД")