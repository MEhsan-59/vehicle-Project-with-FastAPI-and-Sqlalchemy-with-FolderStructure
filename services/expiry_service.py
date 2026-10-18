from datetime import date

from services.maintenance_service import MaintenanceService


class ExpiryService:
    def __init__(self, maintenance_service: MaintenanceService):
        self.maintenance_service = maintenance_service

    def get_expiry_status(self, detail, today: date | None = None):
        today = today or date.today()
        remaining_km = detail.next_changed_km - detail.onground_km
        remaining_days = (detail.next_changed_date - today).days

        expired = remaining_km <= 0 or remaining_days <= 0
        expiring = (
            remaining_km <= detail.km_limit
            or remaining_days <= detail.day_limit
        )
        if not (expired or expiring):
            return None

        status = "expired" if expired else "expiring"
        km_text = (
            f"{remaining_km} km left"
            if remaining_km > 0
            else f"{-remaining_km} km over"
        )
        day_text = (
            f"{remaining_days} days left"
            if remaining_days > 0
            else f"{-remaining_days} days over"
        )
        return {
            "car_no": detail.car_no,
            "model": detail.model,
            "company": detail.company,
            "part": detail.part,
            "status": status,
            "remaining_km": remaining_km,
            "remaining_days": remaining_days,
            "next_changed_km": detail.next_changed_km,
            "next_changed_date": detail.next_changed_date,
            "message": (
                f"{detail.car_no} - {detail.part} {status.upper()}: "
                f"{km_text}, {day_text}"
            ),
        }

    def get_all_expiry(self, user_id: str, today: date | None = None):
        statuses = []
        for detail in self.maintenance_service.get_vehicle_details(user_id):
            status = self.get_expiry_status(detail, today)
            if status is not None:
                statuses.append(status)
        statuses.sort(
            key=lambda status: (
                status["status"] != "expired",
                status["remaining_days"],
                status["remaining_km"],
            )
        )
        return statuses
