from sqlalchemy import Column, DateTime, Integer, String, func

from core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(String, unique=True, index=True, nullable=False)
    user_name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
