from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from datetime import datetime
import uuid
from database.models.base import AlchemyBaseModel

class Order(AlchemyBaseModel):
    __tablename__ = "orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'))  # Связь с users.id (primary key)
    description = Column(Text)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    thread_id = Column(Integer, nullable=True)
    user_message_id = Column(Integer, nullable=True)
    
    # Убираем relationship чтобы избежать проблем