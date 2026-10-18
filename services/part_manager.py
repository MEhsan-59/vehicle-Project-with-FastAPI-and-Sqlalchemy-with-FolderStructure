from repositories.part_repository import PartRepository


class PartManager:
    def __init__(self, repository: PartRepository):
        self.repository = repository

    def get_all_parts(self, user_id: str):
        return self.repository.get_all(user_id)

    def add_part(
        self,
        user_id: str,
        part: str,
        km_life: int,
        month_life: int,
        km_limit: int,
        day_limit: int,
    ):
        if self.repository.get_effective(part, user_id) is not None:
            return {"status": False, "message": "Part already exists."}

        created = self.repository.create(
            user_id, part, km_life, month_life, km_limit, day_limit
        )
        if created is None:
            return {"status": False, "message": "Part already exists."}
        return {"status": True, "message": "Part added successfully."}

    def update_part(
        self,
        user_id: str,
        part: str,
        km_life: int,
        month_life: int,
        km_limit: int,
        day_limit: int,
    ):
        existing = self.repository.get_effective(part, user_id)
        if existing is None:
            return {"status": False, "message": "Part not found."}

        if existing.user_id == user_id:
            self.repository.update(existing, km_life, month_life, km_limit, day_limit)
        else:
            override = self.repository.create_override(
                existing, user_id, km_life, month_life, km_limit, day_limit
            )
            if override is None:
                own = self.repository.get_by_name(user_id, part)
                if own is None:
                    return {"status": False, "message": "Part update failed."}
                self.repository.update(own, km_life, month_life, km_limit, day_limit)
        return {"status": True, "message": "Part updated successfully."}

    def delete_part(self, user_id: str, part: str):
        existing = self.repository.get_by_name(user_id, part)
        if existing is None:
            return {"status": False, "message": "Part not found."}

        used = self.repository.count_usage(existing.id, user_id)
        if used:
            return {
                "status": False,
                "message": f"Part is in use by {used} record(s) and cannot be deleted.",
            }

        self.repository.delete(existing)
        return {"status": True, "message": "Part deleted successfully."}
