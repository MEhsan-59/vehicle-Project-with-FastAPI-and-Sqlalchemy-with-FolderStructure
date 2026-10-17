from sqlalchemy import Column, Integer, String

from core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    user_name = Column(String, nullable=False)
    password = Column(String, nullable=False)
