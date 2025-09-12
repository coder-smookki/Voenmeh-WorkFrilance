from sqlalchemy import String, Integer, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import AlchemyBaseModel

class Bachelor(AlchemyBaseModel):
    __tablename__ = "bachelor"

    id: Mapped[int] = mapped_column(
        Integer(),
        primary_key=True,
        autoincrement=True
    )

    lvl_education: Mapped[int] = mapped_column(
        Integer(),
        nullable=False
    )

    course: Mapped[int] = mapped_column(
        Integer(),
        nullable=False
    )

    discipline: Mapped[str] = mapped_column(
        String(),
        nullable=False
    )

    file_work: Mapped[bytes] = mapped_column(
        LargeBinary(),
        nullable=False
    )