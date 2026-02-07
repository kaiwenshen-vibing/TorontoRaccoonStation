from app.core.errors import FeatureNotImplementedError
from app.services.base import BaseService


class ConflictService(BaseService):
    async def get_booking_conflicts(self, booking_id: int) -> tuple[bool, int, list[int]]:
        raise FeatureNotImplementedError("get_booking_conflicts is not implemented yet.")

