from sqlalchemy.ext.asyncio import AsyncSession
from database.repo.user import UserRepo, OrderRepo
from sqlalchemy import select, update
from typing import List, Optional
from datetime import datetime

# Добавьте этот класс исключения (если еще не добавили)
class ApiError(Exception):
    """Базовое исключение для ошибок API"""
    pass

class RequestsRepo:
    """
    Агрегирующий репозиторий для удобного доступа ко всем репозиториям
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepo(session)
        self.orders = OrderRepo(session)
    
    async def create_order(
        self, 
        user_id: int, 
        product_name: str, 
        quantity: int, 
        price: float,
        thread_id: Optional[int] = None,
        user_message_id: Optional[int] = None
    ) -> int:
        """
        Создание нового заказа
        """
        from database.models.order import Order  # Импорт здесь чтобы избежать циклических импортов
        
        try:
            new_order = Order(
                user_id=user_id,
                product_name=product_name,
                quantity=quantity,
                price=price,
                thread_id=thread_id,
                user_message_id=user_message_id,
                created_at=datetime.now()
            )
            
            self.session.add(new_order)
            await self.session.commit()
            await self.session.refresh(new_order)
            
            return new_order.id
            
        except Exception as e:
            await self.session.rollback()
            raise ApiError(f"Error creating order: {str(e)}")
    
    async def get_order_by_id(self, order_id: int):
        """
        Получение заказа по ID
        """
        from database.models.order import Order
        
        try:
            result = await self.session.execute(
                select(Order).where(Order.id == order_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise ApiError(f"Error getting order: {str(e)}")
    
    async def update_order_message_ids(
        self, 
        order_id: int, 
        thread_id: int, 
        user_message_id: int
    ) -> bool:
        """
        Обновление thread_id и user_message_id для заказа
        """
        from database.models.order import Order
        
        try:
            await self.session.execute(
                update(Order)
                .where(Order.id == order_id)
                .values(thread_id=thread_id, user_message_id=user_message_id)
            )
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise ApiError(f"Error updating order: {str(e)}")
    
    async def get_user_orders(self, user_id: int) -> List:
        """
        Получение всех заказов пользователя
        """
        from database.models.order import Order
        
        try:
            result = await self.session.execute(
                select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
            )
            return result.scalars().all()
            
        except Exception as e:
            raise ApiError(f"Error getting user orders: {str(e)}")
    
    async def update_order_status(self, order_id: int, status: str) -> bool:
        """
        Обновление статуса заказа
        """
        from database.models.order import Order
        
        try:
            await self.session.execute(
                update(Order)
                .where(Order.id == order_id)
                .values(status=status, updated_at=datetime.now())
            )
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise ApiError(f"Error updating order status: {str(e)}")