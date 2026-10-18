from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Vehicle


class VehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_car_no(self, car_no: str, user_id: str) -> Vehicle | None:
        return (
            self.db.query(Vehicle)
            .filter(Vehicle.car_no == car_no, Vehicle.active_user == user_id)
            .first()
        )

    def create(self, vehicle: Vehicle) -> Vehicle | None:
        try:
            self.db.add(vehicle)
            self.db.commit()
            self.db.refresh(vehicle)
        except IntegrityError:
            self.db.rollback()
            return None
        return vehicle

    def update(self, vehicle: Vehicle, onground_km: int) -> Vehicle:
        vehicle.onground_km = onground_km
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def delete(self, vehicle: Vehicle) -> None:
        self.db.delete(vehicle)
        self.db.commit()
