from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.slot import CreateSlotRequest, SlotItem, SlotListResponse, UpdateSlotRequest
from app.services.base import BaseService


class SlotService(BaseService):
    async def _assert_store_exists(self, store_id: int) -> None:
        result = await self.session.execute(
            text("SELECT 1 FROM store WHERE store_id = :store_id"),
            {"store_id": store_id},
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundError(f"store_id={store_id} was not found.")

    async def list_slots(self, store_id: int, limit: int, offset: int) -> SlotListResponse:
        await self._assert_store_exists(store_id=store_id)
        items_result = await self.session.execute(
            text(
                """
                SELECT slot_id, store_id, start_at
                FROM slot
                WHERE store_id = :store_id
                ORDER BY start_at DESC, slot_id DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {"store_id": store_id, "limit": limit, "offset": offset},
        )
        items = [SlotItem(**row) for row in items_result.mappings().all()]
        total_result = await self.session.execute(
            text("SELECT count(*) FROM slot WHERE store_id = :store_id"),
            {"store_id": store_id},
        )
        total = total_result.scalar_one()
        return SlotListResponse(items=items, limit=limit, offset=offset, total=total)

    async def create_slot(self, store_id: int, payload: CreateSlotRequest) -> SlotItem:
        await self._assert_store_exists(store_id=store_id)
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    text(
                        """
                        INSERT INTO slot (store_id, start_at)
                        VALUES (:store_id, :start_at)
                        RETURNING slot_id, store_id, start_at
                        """
                    ),
                    {"store_id": store_id, **payload.model_dump()},
                )
                row = result.mappings().one()
        except IntegrityError as exc:
            raise ConflictError("slot already exists for this start_at.") from exc
        return SlotItem(**row)

    async def update_slot(self, store_id: int, slot_id: int, payload: UpdateSlotRequest) -> SlotItem:
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    text(
                        """
                        UPDATE slot
                        SET start_at = :start_at,
                            updated_at = now()
                        WHERE store_id = :store_id
                          AND slot_id = :slot_id
                        RETURNING slot_id, store_id, start_at
                        """
                    ),
                    {"store_id": store_id, "slot_id": slot_id, "start_at": payload.start_at},
                )
                row = result.mappings().one_or_none()
                if row is None:
                    raise NotFoundError(
                        f"store_id={store_id} does not have slot_id={slot_id}."
                    )
        except IntegrityError as exc:
            raise ConflictError("slot already exists for this start_at.") from exc
        return SlotItem(**row)

    async def delete_slot(self, store_id: int, slot_id: int) -> None:
        async with self.session.begin():
            booking_result = await self.session.execute(
                text(
                    """
                    SELECT 1
                    FROM booking
                    WHERE store_id = :store_id
                      AND slot_id = :slot_id
                      AND booking_status_id IN (2, 4)
                    LIMIT 1
                    """
                ),
                {"store_id": store_id, "slot_id": slot_id},
            )
            if booking_result.scalar_one_or_none() is not None:
                raise ConflictError(f"slot_id={slot_id} has scheduled/completed bookings.")

            result = await self.session.execute(
                text(
                    """
                    DELETE FROM slot
                    WHERE store_id = :store_id
                      AND slot_id = :slot_id
                    RETURNING slot_id
                    """
                ),
                {"store_id": store_id, "slot_id": slot_id},
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError(f"store_id={store_id} does not have slot_id={slot_id}.")
