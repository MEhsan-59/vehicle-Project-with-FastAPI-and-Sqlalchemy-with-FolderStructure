from sqlalchemy import Column, Date, ForeignKey, Integer, UniqueConstraint

from core.database import Base


class Maintenance(Base):
    __tablename__ = "maintenance"
    __table_args__ = (
        UniqueConstraint("vehicle_id", "part_id", name="uq_vehicle_part"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(
        Integer,
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    part_id = Column(
        Integer,
        ForeignKey("parts.id", ondelete="CASCADE"),
        nullable=False,
    )
    changed_km = Column(Integer, nullable=False)
    next_changed_km = Column(Integer, nullable=False)
    changed_date = Column(Date, nullable=False)
    next_changed_date = Column(Date, nullable=False)
