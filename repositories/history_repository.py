from sqlalchemy.orm import Session

from models import History


class HistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def _newest_first(self, query) -> list[History]:
        return query.order_by(
            History.action_timestamp.desc(),
            History.id.desc(),
        ).all()

    def get_all(self, user_id: str) -> list[History]:
        return self._newest_first(
            self.db.query(History).filter(History.active_user == user_id)
        )

    def get_by_car(self, car_no: str, user_id: str) -> list[History]:
        return self._newest_first(
            self.db.query(History).filter(
                History.active_user == user_id,
                History.car_no == car_no,
            )
        )

    def get_by_part(self, part_name: str, user_id: str) -> list[History]:
        return self._newest_first(
            self.db.query(History).filter(
                History.active_user == user_id,
                History.part_name == part_name,
            )
        )
