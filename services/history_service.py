from repositories.history_repository import HistoryRepository


class HistoryService:
    def __init__(self, repository: HistoryRepository):
        self.repository = repository

    def get_history(
        self,
        filter_type: str,
        value: str | None,
        user_id: str,
    ):
        if filter_type == "car":
            if value is None:
                raise ValueError("Value is required for car and part filters.")
            return self.repository.get_by_car(value, user_id)
        if filter_type == "part":
            if value is None:
                raise ValueError("Value is required for car and part filters.")
            return self.repository.get_by_part(value, user_id)
        return self.repository.get_all(user_id)
