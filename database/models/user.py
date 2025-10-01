from sqlalchemy import String, BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import AlchemyBaseModel

class User(AlchemyBaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer(),
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger(),
        nullable=False
    )

    chat_id: Mapped[int] = mapped_column(
        BigInteger(),
        nullable=False
    )

    count_proposed_works: Mapped[int] = mapped_column(
        Integer(),
        nullable=False
    )

    count_works_ordered: Mapped[int] = mapped_column(
        Integer(),
        nullable=False
    )

    list_order: Mapped[str] = mapped_column(
        String(),
        nullable=True
    )