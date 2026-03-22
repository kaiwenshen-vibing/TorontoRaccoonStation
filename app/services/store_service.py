from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.store import CreateStoreRequest, StoreItem, StoreListResponse, UpdateStoreRequest
from app.services.base import BaseService


class StoreService(BaseService):
    async def list_stores(
        self, allowed_store_ids: set[int], limit: int, offset: int
    ) -> StoreListResponse:
        store_ids = sorted(allowed_store_ids)
        items_result = await self.session.execute(
            text(
                """
                SELECT store_id, name, pic_storage_key
                FROM store
                WHERE store_id = ANY(:allowed_store_ids)
                ORDER BY updated_at DESC, store_id DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {"allowed_store_ids": store_ids, "limit": limit, "offset": offset},
        )
        items = [StoreItem(**row) for row in items_result.mappings().all()]
        total_result = await self.session.execute(
            text("SELECT count(*) FROM store WHERE store_id = ANY(:allowed_store_ids)"),
            {"allowed_store_ids": store_ids},
        )
        total = total_result.scalar_one()
        return StoreListResponse(items=items, limit=limit, offset=offset, total=total)

    async def get_store(self, store_id: int) -> StoreItem:
        result = await self.session.execute(
            text(
                """
                SELECT store_id, name, pic_storage_key
                FROM store
                WHERE store_id = :store_id
                """
            ),
            {"store_id": store_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise NotFoundError(f"store_id={store_id} was not found.")
        return StoreItem(**row)

    async def create_store(self, payload: CreateStoreRequest) -> StoreItem:
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    text(
                        """
                        INSERT INTO store (name, pic_storage_key)
                        VALUES (:name, :pic_storage_key)
                        RETURNING store_id, name, pic_storage_key
                        """
                    ),
                    payload.model_dump(),
                )
                row = result.mappings().one()
        except IntegrityError as exc:
            raise ConflictError("store could not be created.") from exc
        return StoreItem(**row)

    async def update_store(self, store_id: int, payload: UpdateStoreRequest) -> StoreItem:
        values = {"store_id": store_id}
        updates = []
        if "name" in payload.model_fields_set:
            updates.append("name = :name")
            values["name"] = payload.name
        if "pic_storage_key" in payload.model_fields_set:
            updates.append("pic_storage_key = :pic_storage_key")
            values["pic_storage_key"] = payload.pic_storage_key
        updates.append("updated_at = now()")
        query = f"""
            UPDATE store
            SET {", ".join(updates)}
            WHERE store_id = :store_id
            RETURNING store_id, name, pic_storage_key
        """
        async with self.session.begin():
            result = await self.session.execute(text(query), values)
            row = result.mappings().one_or_none()
            if row is None:
                raise NotFoundError(f"store_id={store_id} was not found.")
        return StoreItem(**row)

    async def delete_store(self, store_id: int) -> None:
        async with self.session.begin():
            exists_result = await self.session.execute(
                text("SELECT 1 FROM store WHERE store_id = :store_id"),
                {"store_id": store_id},
            )
            if exists_result.scalar_one_or_none() is None:
                raise NotFoundError(f"store_id={store_id} was not found.")

            dependency_checks = (
                ("store_room", "store has rooms."),
                ("slot", "store has slots."),
                ("booking", "store has bookings."),
                ("store_script", "store has script mappings."),
            )
            for table_name, message in dependency_checks:
                result = await self.session.execute(
                    text(f"SELECT 1 FROM {table_name} WHERE store_id = :store_id LIMIT 1"),
                    {"store_id": store_id},
                )
                if result.scalar_one_or_none() is not None:
                    raise ConflictError(message)

            result = await self.session.execute(
                text("DELETE FROM store WHERE store_id = :store_id RETURNING store_id"),
                {"store_id": store_id},
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError(f"store_id={store_id} was not found.")
