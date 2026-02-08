from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.script import (
    CreateScriptRequest,
    CreateStoreScriptRequest,
    ScriptItem,
    ScriptListResponse,
    StoreScriptItem,
    StoreScriptListResponse,
    UpdateScriptRequest,
    UpdateStoreScriptRequest,
)
from app.services.base import BaseService


class ScriptService(BaseService):
    async def list_scripts(self, limit: int, offset: int) -> ScriptListResponse:
        items_result = await self.session.execute(
            text(
                """
                SELECT script_id, name, estimated_minutes
                FROM script
                ORDER BY updated_at DESC, script_id DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {"limit": limit, "offset": offset},
        )
        items = [ScriptItem(**row) for row in items_result.mappings().all()]
        total_result = await self.session.execute(text("SELECT count(*) FROM script"))
        total = total_result.scalar_one()
        return ScriptListResponse(items=items, limit=limit, offset=offset, total=total)

    async def get_script(self, script_id: int) -> ScriptItem:
        result = await self.session.execute(
            text(
                """
                SELECT script_id, name, estimated_minutes
                FROM script
                WHERE script_id = :script_id
                """
            ),
            {"script_id": script_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise NotFoundError(f"script_id={script_id} was not found.")
        return ScriptItem(**row)

    async def create_script(self, payload: CreateScriptRequest) -> ScriptItem:
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    text(
                        """
                        INSERT INTO script (name, estimated_minutes)
                        VALUES (:name, :estimated_minutes)
                        RETURNING script_id, name, estimated_minutes
                        """
                    ),
                    payload.model_dump(),
                )
                row = result.mappings().one()
        except IntegrityError as exc:
            raise ConflictError("script name already exists.") from exc
        return ScriptItem(**row)

    async def update_script(self, script_id: int, payload: UpdateScriptRequest) -> ScriptItem:
        values = {"script_id": script_id}
        updates = []
        if payload.name is not None:
            updates.append("name = :name")
            values["name"] = payload.name
        if payload.estimated_minutes is not None:
            updates.append("estimated_minutes = :estimated_minutes")
            values["estimated_minutes"] = payload.estimated_minutes
        updates.append("updated_at = now()")
        query = f"""
            UPDATE script
            SET {", ".join(updates)}
            WHERE script_id = :script_id
            RETURNING script_id, name, estimated_minutes
        """
        try:
            async with self.session.begin():
                result = await self.session.execute(text(query), values)
                row = result.mappings().one_or_none()
                if row is None:
                    raise NotFoundError(f"script_id={script_id} was not found.")
        except IntegrityError as exc:
            raise ConflictError("script name already exists.") from exc
        return ScriptItem(**row)

    async def delete_script(self, script_id: int) -> None:
        async with self.session.begin():
            exists_result = await self.session.execute(
                text("SELECT 1 FROM script WHERE script_id = :script_id"),
                {"script_id": script_id},
            )
            if exists_result.scalar_one_or_none() is None:
                raise NotFoundError(f"script_id={script_id} was not found.")

            booking_result = await self.session.execute(
                text(
                    """
                    SELECT 1
                    FROM booking
                    WHERE script_id = :script_id
                    LIMIT 1
                    """
                ),
                {"script_id": script_id},
            )
            if booking_result.scalar_one_or_none() is not None:
                raise ConflictError("script is referenced by existing bookings.")

            active_result = await self.session.execute(
                text(
                    """
                    SELECT 1
                    FROM store_script
                    WHERE script_id = :script_id
                      AND is_active = true
                    LIMIT 1
                    """
                ),
                {"script_id": script_id},
            )
            if active_result.scalar_one_or_none() is not None:
                raise ConflictError("script is active for at least one store.")

            await self.session.execute(
                text("DELETE FROM store_script WHERE script_id = :script_id"),
                {"script_id": script_id},
            )
            await self.session.execute(
                text("DELETE FROM script WHERE script_id = :script_id"),
                {"script_id": script_id},
            )

    async def list_store_scripts(
        self, store_id: int, limit: int, offset: int
    ) -> StoreScriptListResponse:
        items_result = await self.session.execute(
            text(
                """
                SELECT s.script_id, s.name, s.estimated_minutes, ss.is_active
                FROM store_script AS ss
                JOIN script AS s ON s.script_id = ss.script_id
                WHERE ss.store_id = :store_id
                ORDER BY ss.updated_at DESC, s.script_id DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {"store_id": store_id, "limit": limit, "offset": offset},
        )
        items = [StoreScriptItem(**row) for row in items_result.mappings().all()]
        total_result = await self.session.execute(
            text("SELECT count(*) FROM store_script WHERE store_id = :store_id"),
            {"store_id": store_id},
        )
        total = total_result.scalar_one()
        return StoreScriptListResponse(items=items, limit=limit, offset=offset, total=total)

    async def create_store_script(
        self, store_id: int, payload: CreateStoreScriptRequest
    ) -> StoreScriptItem:
        async with self.session.begin():
            store_exists = await self.session.execute(
                text("SELECT 1 FROM store WHERE store_id = :store_id"),
                {"store_id": store_id},
            )
            if store_exists.scalar_one_or_none() is None:
                raise NotFoundError(f"store_id={store_id} was not found.")

            script_exists = await self.session.execute(
                text("SELECT 1 FROM script WHERE script_id = :script_id"),
                {"script_id": payload.script_id},
            )
            if script_exists.scalar_one_or_none() is None:
                raise NotFoundError(f"script_id={payload.script_id} was not found.")

            existing = await self.session.execute(
                text(
                    """
                    SELECT 1
                    FROM store_script
                    WHERE store_id = :store_id
                      AND script_id = :script_id
                    """
                ),
                {"store_id": store_id, "script_id": payload.script_id},
            )
            if existing.scalar_one_or_none() is not None:
                raise ConflictError(
                    f"store_id={store_id} already has script_id={payload.script_id}."
                )

            await self.session.execute(
                text(
                    """
                    INSERT INTO store_script (store_id, script_id, is_active)
                    VALUES (:store_id, :script_id, :is_active)
                    """
                ),
                {
                    "store_id": store_id,
                    "script_id": payload.script_id,
                    "is_active": payload.is_active,
                },
            )

            result = await self.session.execute(
                text(
                    """
                    SELECT s.script_id, s.name, s.estimated_minutes, ss.is_active
                    FROM store_script AS ss
                    JOIN script AS s ON s.script_id = ss.script_id
                    WHERE ss.store_id = :store_id
                      AND ss.script_id = :script_id
                    """
                ),
                {"store_id": store_id, "script_id": payload.script_id},
            )
            row = result.mappings().one()
        return StoreScriptItem(**row)

    async def update_store_script(
        self, store_id: int, script_id: int, payload: UpdateStoreScriptRequest
    ) -> StoreScriptItem:
        async with self.session.begin():
            result = await self.session.execute(
                text(
                    """
                    UPDATE store_script
                    SET is_active = :is_active,
                        updated_at = now()
                    WHERE store_id = :store_id
                      AND script_id = :script_id
                    RETURNING store_id
                    """
                ),
                {"store_id": store_id, "script_id": script_id, "is_active": payload.is_active},
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError(
                    f"store_id={store_id} does not have script_id={script_id}."
                )

            item_result = await self.session.execute(
                text(
                    """
                    SELECT s.script_id, s.name, s.estimated_minutes, ss.is_active
                    FROM store_script AS ss
                    JOIN script AS s ON s.script_id = ss.script_id
                    WHERE ss.store_id = :store_id
                      AND ss.script_id = :script_id
                    """
                ),
                {"store_id": store_id, "script_id": script_id},
            )
            row = item_result.mappings().one()
        return StoreScriptItem(**row)

    async def delete_store_script(self, store_id: int, script_id: int) -> None:
        async with self.session.begin():
            booking_result = await self.session.execute(
                text(
                    """
                    SELECT 1
                    FROM booking
                    WHERE store_id = :store_id
                      AND script_id = :script_id
                    LIMIT 1
                    """
                ),
                {"store_id": store_id, "script_id": script_id},
            )
            if booking_result.scalar_one_or_none() is not None:
                raise ConflictError(
                    f"store_id={store_id} has bookings for script_id={script_id}."
                )

            result = await self.session.execute(
                text(
                    """
                    DELETE FROM store_script
                    WHERE store_id = :store_id
                      AND script_id = :script_id
                    RETURNING store_id
                    """
                ),
                {"store_id": store_id, "script_id": script_id},
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError(
                    f"store_id={store_id} does not have script_id={script_id}."
                )
