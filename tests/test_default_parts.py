import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-for-auth-tests")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from core.database import Base
from models import Part
from repositories.part_repository import PartRepository
from services.default_part_service import seed_default_parts
from services.part_service import PartService


DEFAULT_PARTS = [
    {
        "part": "battery",
        "km_life": 3000,
        "month_life": 6,
        "km_limit": 300,
        "day_limit": 30,
    },
    {
        "part": "oil filter",
        "km_life": 5000,
        "month_life": 6,
        "km_limit": 200,
        "day_limit": 15,
    },
]


def test_defaults_are_shared_and_user_overrides_are_private():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        seed_default_parts(db, DEFAULT_PARTS)
        service = PartService(PartRepository(db))

        first_user_parts = service.get_all_parts("first-user")
        assert [(part.part, part.is_default) for part in first_user_parts] == [
            ("battery", True),
            ("oil filter", True),
        ]

        result = service.update_part("first-user", "battery", 6000, 12, 300, 30)
        assert result == {"status": True, "message": "Part updated successfully."}

        first_battery = next(
            part for part in service.get_all_parts("first-user")
            if part.part == "battery"
        )
        second_battery = next(
            part for part in service.get_all_parts("second-user")
            if part.part == "battery"
        )
        assert (first_battery.km_life, first_battery.is_default) == (6000, False)
        assert (second_battery.km_life, second_battery.is_default) == (3000, True)
        assert db.query(Part).filter(Part.part == "battery").count() == 2
    engine.dispose()


def test_deleting_override_restores_default_and_default_cannot_be_deleted():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        seed_default_parts(db, DEFAULT_PARTS)
        service = PartService(PartRepository(db))

        result = service.delete_part("first-user", "battery")
        assert result == {"status": False, "message": "Part not found."}

        service.update_part("first-user", "battery", 6000, 12, 300, 30)
        result = service.delete_part("first-user", "battery")

        assert result == {"status": True, "message": "Part deleted successfully."}
        battery = next(
            part for part in service.get_all_parts("first-user")
            if part.part == "battery"
        )
        assert (battery.km_life, battery.is_default) == (3000, True)
    engine.dispose()


def test_default_seeding_is_repeatable_and_updates_default_values():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        assert seed_default_parts(db, DEFAULT_PARTS) == 2
        assert seed_default_parts(db, DEFAULT_PARTS) == 0
        updated_defaults = [
            {**DEFAULT_PARTS[0], "km_life": 4000},
            DEFAULT_PARTS[1],
        ]

        assert seed_default_parts(db, updated_defaults) == 1
        assert (
            db.query(Part)
            .filter(Part.part == "battery", Part.user_id.is_(None))
            .one()
            .km_life
            == 4000
        )
    engine.dispose()
