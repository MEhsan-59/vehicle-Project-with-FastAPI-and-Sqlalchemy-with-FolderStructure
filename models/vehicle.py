from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from core.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    car_no = Column(String, nullable=False, unique=True, index=True)
    model = Column(String, nullable=False)
    company = Column(String, nullable=False)
    onground_km = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    active_user = Column(
        String,
        ForeignKey("accounts.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
