from app.core.errors import FeatureNotImplementedError
from app.schemas.slot import CreateSlotRequest, SlotItem, SlotListResponse, UpdateSlotRequest
from app.services.base import BaseService


class SlotService(BaseService):
    async def list_slots(self, store_id: int, limit: int, offset: int) -> SlotListResponse:
        raise FeatureNotImplementedError("list_slots is not implemented yet.")

    async def create_slot(self, store_id: int, payload: CreateSlotRequest) -> SlotItem:
        raise FeatureNotImplementedError("create_slot is not implemented yet.")

    async def update_slot(self, store_id: int, slot_id: int, payload: UpdateSlotRequest) -> SlotItem:
        raise FeatureNotImplementedError("update_slot is not implemented yet.")

    async def delete_slot(self, store_id: int, slot_id: int) -> None:
        raise FeatureNotImplementedError("delete_slot is not implemented yet.")

