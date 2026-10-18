from calendar import monthrange
from datetime import date

from models import History
from repositories.maintenance_repository import MaintenanceRepository
from repositories.part_repository import PartRepository
from repositories.vehicle_repository import VehicleRepository


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


class MaintenanceService:
    def __init__(
        self,
        vehicle_repository: VehicleRepository,
        maintenance_repository: MaintenanceRepository,
        part_repository: PartRepository,
    ):
        self.vehicle_repository = vehicle_repository
        self.maintenance_repository = maintenance_repository
        self.part_repository = part_repository

    def update_part(
        self,
        car_no: str,
        part: str,
        changed_km: int,
        changed_date: date,
        user_id: str,
    ) -> tuple[bool, str]:
        vehicle = self.vehicle_repository.get_by_car_no(car_no, user_id)
        if vehicle is None:
            return False, "Car not found."

        part_config = self.part_repository.get_effective(part, user_id)
        if part_config is None:
            return False, "Part not found."
        if changed_date > date.today():
            return False, "Future date not allowed."
        if changed_km > vehicle.onground_km:
            return False, "New change km must be less than on ground km."

        next_changed_km = changed_km + part_config.km_life
        next_changed_date = add_months(changed_date, part_config.month_life)
        history = History(
            vehicle_id=vehicle.id,
            car_no=vehicle.car_no,
            part_name=part,
            changed_km=changed_km,
            changed_date=changed_date,
            active_user=user_id,
            details=(
                f"Next KM: {next_changed_km}, "
                f"Next Date: {next_changed_date.isoformat()}"
            ),
        )
        self.maintenance_repository.upsert(
            vehicle.id,
            part_config.id,
            changed_km,
            next_changed_km,
            changed_date,
            next_changed_date,
            history,
        )
        return True, f"{part} updated successfully."

    def get_vehicle_details(
        self,
        user_id: str,
        filter_type: str = "all",
        value: str | None = None,
    ):
        return self.maintenance_repository.get_details(
            user_id,
            filter_type,
            value,
        )
