from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from database.models.base import AlchemyBaseModel
import json
from datetime import datetime

class PendingSubmission(AlchemyBaseModel):
    __tablename__ = "pending_submissions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)  # UUID из submission_data
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    lvl_education: Mapped[str] = mapped_column(String(50), nullable=False)
    course: Mapped[str] = mapped_column(String(50), nullable=False)
    work_name: Mapped[str] = mapped_column(String(200), nullable=False)
    files_data: Mapped[str] = mapped_column(Text, nullable=True)  # JSON с информацией о файлах
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)