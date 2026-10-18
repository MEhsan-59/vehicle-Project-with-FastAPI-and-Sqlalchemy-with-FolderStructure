from models import Vehicle
from repositories.vehicle_repository import VehicleRepository


class VehicleService:
    def __init__(
        self,
        repository: VehicleRepository,
    ):
        self.repository = repository

    def add_car(
        self,
        car_no: str,
        model: str,
        company: str,
        onground_km: int,
        user_id: str,
    ) -> tuple[bool, str]:
        vehicle = Vehicle(
            car_no=car_no,
            model=model,
            company=company,
            onground_km=onground_km,
            active_user=user_id,
        )
        if self.repository.create(vehicle) is None:
            return False, "Car already exists."
        return True, "Car added successfully."

    def delete_car(self, car_no: str, user_id: str) -> tuple[bool, str]:
        vehicle = self.repository.get_by_car_no(car_no, user_id)
        if vehicle is None:
            return False, "Car not found."
        self.repository.delete(vehicle)
        return True, "Car deleted successfully."

    def update_km(
        self, car_no: str, onground_km: int, user_id: str
    ) -> tuple[bool, str]:
        vehicle = self.repository.get_by_car_no(car_no, user_id)
        if vehicle is None:
            return False, "Car not found."
        if vehicle.onground_km > onground_km:
            return (
                False,
                f"Onground km must not be less than old km {vehicle.onground_km}.",
            )
        old_km = vehicle.onground_km
        self.repository.update(vehicle, onground_km, old_km)
        return True, "Onground km updated successfully."
