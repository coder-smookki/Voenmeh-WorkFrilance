from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from database.models.base import AlchemyBaseModel

class WorkFile(AlchemyBaseModel):
    __tablename__ = "work_files"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_work_id: Mapped[int] = mapped_column(ForeignKey("student_works.id"), nullable=False) # Изменено с bachelor_id
    file_field: Mapped[str] = mapped_column(String(50), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)