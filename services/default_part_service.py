from models import Part


def seed_default_parts(db, default_parts: list[dict[str, str | int]]) -> int:
    changed = 0
    for values in default_parts:
        part = (
            db.query(Part)
            .filter(Part.part == values["part"], Part.user_id.is_(None))
            .first()
        )
        if part is None:
            db.add(Part(user_id=None, **values))
            changed += 1
        elif any(getattr(part, key) != value for key, value in values.items()):
            for key, value in values.items():
                setattr(part, key, value)
            changed += 1
    db.commit()
    return changed
