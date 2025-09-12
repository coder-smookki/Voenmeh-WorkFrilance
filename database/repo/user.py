from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from database.models import User
from database.exceptions import NotFoundException

# TODO add transaction
class UserRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def set(self, user_id: int, chat_id: int, count_proposed_works: int, 
                  count_works_ordered: int, list_order: str) -> None:
        """Устанавливает данные юзера"""
        user = User(
            id=user_id,
            chat_id=chat_id,
            count_proposed_works=count_proposed_works,
            count_works_ordered=count_works_ordered,
            list_order=list_order
        )
        self.session.add(user)
        await self.session.commit()

    async def get(self, user_id: int) -> User:
        """Возращает юзера по юзер айди"""
        user = await self.session.scalar(select(User).where(User.id == user_id))
        if user is None:
            raise NotFoundException
        return user

    async def get_order_count(self, user_id: int) -> int:
        """Возвращает количество заказов у пользователя"""
        user = await self.get(user_id)
        return user.count_works_ordered

    async def get_order_list(self, user_id: int) -> list[str]:
        """Возвращает список заказов пользователя в виде массива строк"""
        user = await self.get(user_id)
        if not user.list_order:
            return []
        return user.list_order.split(',')

    async def get_uploaded_works_count(self, user_id: int) -> int:
        """Возвращает количество загруженных работ пользователя"""
        user = await self.get(user_id)
        return user.count_proposed_works