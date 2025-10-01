from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from database.models.base import AlchemyBaseModel

class StudentWork(AlchemyBaseModel):
    __tablename__ = "student_works"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    education_level: Mapped[int] = mapped_column(Integer, nullable=False)
    course: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(String(150), nullable=False)
    work_name: Mapped[str] = mapped_column(String(300), nullable=False)
    archive_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)