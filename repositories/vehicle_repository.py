from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import History, Maintenance, Vehicle


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
            self.db.flush()
            self.db.add(
                History(
                    vehicle_id=vehicle.id,
                    car_no=vehicle.car_no,
                    action_type="car_added",
                    active_user=vehicle.active_user,
                    details=(
                        f"{vehicle.company} {vehicle.model}, "
                        f"{vehicle.onground_km} km"
                    ),
                )
            )
            self.db.commit()
            self.db.refresh(vehicle)
        except IntegrityError:
            self.db.rollback()
            return None
        return vehicle

    def update(
        self,
        vehicle: Vehicle,
        onground_km: int,
        old_km: int,
    ) -> Vehicle:
        vehicle.onground_km = onground_km
        self.db.add(
            History(
                vehicle_id=vehicle.id,
                car_no=vehicle.car_no,
                action_type="km_updated",
                active_user=vehicle.active_user,
                details=f"km: {old_km} -> {onground_km}",
            )
        )
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def delete(self, vehicle: Vehicle) -> None:
        self.db.query(Maintenance).filter(
            Maintenance.vehicle_id == vehicle.id
        ).delete()
        self.db.query(History).filter(History.vehicle_id == vehicle.id).delete()
        self.db.delete(vehicle)
        self.db.commit()
