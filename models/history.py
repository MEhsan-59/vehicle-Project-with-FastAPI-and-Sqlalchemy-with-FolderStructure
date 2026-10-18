from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, func

from core.database import Base


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(
        Integer,
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    car_no = Column(String, nullable=False, index=True)
    action_type = Column(String, nullable=False)
    part_name = Column(String, nullable=True)
    changed_km = Column(Integer, nullable=True)
    changed_date = Column(Date, nullable=True)
    action_timestamp = Column(DateTime(timezone=False), server_default=func.now())
    active_user = Column(
        String,
        ForeignKey("accounts.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    details = Column(String, nullable=True)
