from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Part


class PartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, user_id: str, part: str) -> Part | None:
        return (
            self.db.query(Part)
            .filter(Part.user_id == user_id, Part.part == part)
            .first()
        )

    def get_default(self, part: str) -> Part | None:
        return (
            self.db.query(Part)
            .filter(Part.part == part, Part.user_id.is_(None))
            .first()
        )

    def get_effective(self, part: str, user_id: str) -> Part | None:
        return self.get_by_name(user_id, part) or self.get_default(part)

    def get_all(self, user_id: str) -> list[Part]:
        own = self.db.query(Part).filter(Part.user_id == user_id).all()
        own_names = {part.part for part in own}
        defaults = self.db.query(Part).filter(Part.user_id.is_(None)).all()
        return sorted(
            own + [part for part in defaults if part.part not in own_names],
            key=lambda part: part.part,
        )

    def create(
        self,
        user_id: str,
        part: str,
        km_life: int,
        month_life: int,
        km_limit: int,
        day_limit: int,
    ) -> Part | None:
        part_config = Part(
            user_id=user_id,
            part=part,
            km_life=km_life,
            month_life=month_life,
            km_limit=km_limit,
            day_limit=day_limit,
        )
        try:
            self.db.add(part_config)
            self.db.commit()
            self.db.refresh(part_config)
        except IntegrityError:
            self.db.rollback()
            return None
        return part_config

    def create_override(
        self,
        default_part: Part,
        user_id: str,
        km_life: int,
        month_life: int,
        km_limit: int,
        day_limit: int,
    ) -> Part | None:
        override = Part(
            user_id=user_id,
            part=default_part.part,
            km_life=km_life,
            month_life=month_life,
            km_limit=km_limit,
            day_limit=day_limit,
        )
        try:
            self.db.add(override)
            self.db.flush()
            self.db.commit()
            self.db.refresh(override)
        except IntegrityError:
            self.db.rollback()
            return None
        return override

    def update(
        self,
        part_config: Part,
        km_life: int,
        month_life: int,
        km_limit: int,
        day_limit: int,
    ) -> Part:
        part_config.km_life = km_life
        part_config.month_life = month_life
        part_config.km_limit = km_limit
        part_config.day_limit = day_limit
        self.db.commit()
        self.db.refresh(part_config)
        return part_config

    def delete(self, part_config: Part) -> None:
        self.db.delete(part_config)
        self.db.commit()
