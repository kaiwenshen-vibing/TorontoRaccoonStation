from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.room import CreateRoomRequest, RoomItem, RoomListResponse, UpdateRoomRequest
from app.services.base import BaseService


class RoomService(BaseService):
    async def _assert_store_exists(self, store_id: int) -> None:
        result = await self.session.execute(
            text("SELECT 1 FROM store WHERE store_id = :store_id"),
            {"store_id": store_id},
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundError(f"store_id={store_id} was not found.")

    async def list_rooms(self, store_id: int, limit: int, offset: int) -> RoomListResponse:
        await self._assert_store_exists(store_id=store_id)
        items_result = await self.session.execute(
            text(
                """
                SELECT store_room_id, store_id, name, is_active
                FROM store_room
                WHERE store_id = :store_id
                ORDER BY updated_at DESC, store_room_id DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {"store_id": store_id, "limit": limit, "offset": offset},
        )
        items = [RoomItem(**row) for row in items_result.mappings().all()]
        total_result = await self.session.execute(
            text("SELECT count(*) FROM store_room WHERE store_id = :store_id"),
            {"store_id": store_id},
        )
        total = total_result.scalar_one()
        return RoomListResponse(items=items, limit=limit, offset=offset, total=total)

    async def create_room(self, store_id: int, payload: CreateRoomRequest) -> RoomItem:
        await self._assert_store_exists(store_id=store_id)
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    text(
                        """
                        INSERT INTO store_room (store_id, name)
                        VALUES (:store_id, :name)
                        RETURNING store_room_id, store_id, name, is_active
                        """
                    ),
                    {"store_id": store_id, **payload.model_dump()},
                )
                row = result.mappings().one()
        except IntegrityError as exc:
            raise ConflictError("room name already exists for this store.") from exc
        return RoomItem(**row)

    async def update_room(
        self,
        store_id: int,
        store_room_id: int,
        payload: UpdateRoomRequest,
    ) -> RoomItem:
        values = {"store_id": store_id, "store_room_id": store_room_id}
        updates = []
        if payload.name is not None:
            updates.append("name = :name")
            values["name"] = payload.name
        if payload.is_active is not None:
            updates.append("is_active = :is_active")
            values["is_active"] = payload.is_active
        updates.append("updated_at = now()")
        query = f"""
            UPDATE store_room
            SET {", ".join(updates)}
            WHERE store_id = :store_id
              AND store_room_id = :store_room_id
            RETURNING store_room_id, store_id, name, is_active
        """
        try:
            async with self.session.begin():
                result = await self.session.execute(text(query), values)
                row = result.mappings().one_or_none()
                if row is None:
                    raise NotFoundError(
                        f"store_id={store_id} does not have store_room_id={store_room_id}."
                    )
        except IntegrityError as exc:
            raise ConflictError("room name already exists for this store.") from exc
        return RoomItem(**row)

    async def delete_room(self, store_id: int, store_room_id: int) -> None:
        async with self.session.begin():
            booking_result = await self.session.execute(
                text(
                    """
                    SELECT 1
                    FROM booking
                    WHERE store_id = :store_id
                      AND store_room_id = :store_room_id
                      AND booking_status_id = 2
                    LIMIT 1
                    """
                ),
                {"store_id": store_id, "store_room_id": store_room_id},
            )
            if booking_result.scalar_one_or_none() is not None:
                raise ConflictError(
                    f"store_room_id={store_room_id} has scheduled bookings."
                )

            result = await self.session.execute(
                text(
                    """
                    DELETE FROM store_room
                    WHERE store_id = :store_id
                      AND store_room_id = :store_room_id
                    RETURNING store_room_id
                    """
                ),
                {"store_id": store_id, "store_room_id": store_room_id},
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError(
                    f"store_id={store_id} does not have store_room_id={store_room_id}."
                )
