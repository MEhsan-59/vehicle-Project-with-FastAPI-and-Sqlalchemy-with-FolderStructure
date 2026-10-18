from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import History, Maintenance, Part, Vehicle


class MaintenanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert(
        self,
        vehicle_id: int,
        part_id: int,
        changed_km: int,
        next_changed_km: int,
        changed_date,
        next_changed_date,
        history: History,
    ) -> bool:
        values = {
            "changed_km": changed_km,
            "next_changed_km": next_changed_km,
            "changed_date": changed_date,
            "next_changed_date": next_changed_date,
        }
        record = (
            self.db.query(Maintenance)
            .filter(
                Maintenance.vehicle_id == vehicle_id,
                Maintenance.part_id == part_id,
            )
            .first()
        )
        is_new = record is None
        try:
            if is_new:
                self.db.add(
                    Maintenance(
                        vehicle_id=vehicle_id,
                        part_id=part_id,
                        **values,
                    )
                )
            else:
                for key, value in values.items():
                    setattr(record, key, value)
            history.action_type = "part_added" if is_new else "part_updated"
            self.db.add(history)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            record = (
                self.db.query(Maintenance)
                .filter(
                    Maintenance.vehicle_id == vehicle_id,
                    Maintenance.part_id == part_id,
                )
                .first()
            )
            if record is None:
                raise
            for key, value in values.items():
                setattr(record, key, value)
            history.action_type = "part_updated"
            self.db.add(history)
            self.db.commit()
            is_new = False
        return is_new

    def get_details(
        self,
        user_id: str,
        filter_type: str = "all",
        value: str | None = None,
    ):
        query = (
            self.db.query(
                Vehicle.car_no,
                Vehicle.model,
                Vehicle.company,
                Vehicle.onground_km,
                Part.part.label("part"),
                Part.km_limit,
                Part.day_limit,
                Maintenance.changed_km,
                Maintenance.next_changed_km,
                Maintenance.changed_date,
                Maintenance.next_changed_date,
            )
            .join(Maintenance, Maintenance.vehicle_id == Vehicle.id)
            .join(Part, Part.id == Maintenance.part_id)
            .filter(Vehicle.active_user == user_id)
        )
        if value:
            normalized_value = value.strip().lower()
            if filter_type == "car":
                query = query.filter(
                    func.lower(Vehicle.car_no).contains(
                        normalized_value,
                        autoescape=True,
                    )
                )
            elif filter_type == "part":
                query = query.filter(
                    func.lower(Part.part).contains(
                        normalized_value,
                        autoescape=True,
                    )
                )
        return query.order_by(Vehicle.car_no, Part.part).all()

    def count_usage(self, part_id: int, user_id: str) -> int:
        return (
            self.db.query(func.count(Maintenance.id))
            .join(Vehicle, Maintenance.vehicle_id == Vehicle.id)
            .filter(
                Maintenance.part_id == part_id,
                Vehicle.active_user == user_id,
            )
            .scalar()
            or 0
        )
