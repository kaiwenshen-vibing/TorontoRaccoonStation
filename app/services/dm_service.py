from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.dm import (
    CreateDmRequest,
    CreateDmStoreMembershipRequest,
    DmItem,
    DmListResponse,
    DmStoreMembershipItem,
    DmStoreMembershipListResponse,
    UpdateDmRequest,
)
from app.services.base import BaseService


class DmService(BaseService):
    async def _assert_dm_exists(self, dm_id: int) -> None:
        result = await self.session.execute(
            text("SELECT 1 FROM dm WHERE dm_id = :dm_id"),
            {"dm_id": dm_id},
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundError(f"dm_id={dm_id} was not found.")

    async def list_dms(self, limit: int, offset: int) -> DmListResponse:
        items_result = await self.session.execute(
            text(
                """
                SELECT dm_id, display_name, is_active, pic_storage_key
                FROM dm
                ORDER BY updated_at DESC, dm_id DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {"limit": limit, "offset": offset},
        )
        items = [DmItem(**row) for row in items_result.mappings().all()]
        total_result = await self.session.execute(text("SELECT count(*) FROM dm"))
        total = total_result.scalar_one()
        return DmListResponse(items=items, limit=limit, offset=offset, total=total)

    async def get_dm(self, dm_id: int) -> DmItem:
        result = await self.session.execute(
            text(
                """
                SELECT dm_id, display_name, is_active, pic_storage_key
                FROM dm
                WHERE dm_id = :dm_id
                """
            ),
            {"dm_id": dm_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise NotFoundError(f"dm_id={dm_id} was not found.")
        return DmItem(**row)

    async def create_dm(self, payload: CreateDmRequest) -> DmItem:
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    text(
                        """
                        INSERT INTO dm (display_name, is_active, pic_storage_key)
                        VALUES (:display_name, :is_active, :pic_storage_key)
                        RETURNING dm_id, display_name, is_active, pic_storage_key
                        """
                    ),
                    payload.model_dump(),
                )
                row = result.mappings().one()
        except IntegrityError as exc:
            raise ConflictError("dm could not be created.") from exc
        return DmItem(**row)

    async def update_dm(self, dm_id: int, payload: UpdateDmRequest) -> DmItem:
        values = {"dm_id": dm_id}
        updates = []
        if "display_name" in payload.model_fields_set:
            updates.append("display_name = :display_name")
            values["display_name"] = payload.display_name
        if "is_active" in payload.model_fields_set:
            updates.append("is_active = :is_active")
            values["is_active"] = payload.is_active
        if "pic_storage_key" in payload.model_fields_set:
            updates.append("pic_storage_key = :pic_storage_key")
            values["pic_storage_key"] = payload.pic_storage_key
        updates.append("updated_at = now()")
        query = f"""
            UPDATE dm
            SET {", ".join(updates)}
            WHERE dm_id = :dm_id
            RETURNING dm_id, display_name, is_active, pic_storage_key
        """
        async with self.session.begin():
            result = await self.session.execute(text(query), values)
            row = result.mappings().one_or_none()
            if row is None:
                raise NotFoundError(f"dm_id={dm_id} was not found.")
        return DmItem(**row)

    async def delete_dm(self, dm_id: int) -> None:
        async with self.session.begin():
            exists_result = await self.session.execute(
                text("SELECT 1 FROM dm WHERE dm_id = :dm_id"),
                {"dm_id": dm_id},
            )
            if exists_result.scalar_one_or_none() is None:
                raise NotFoundError(f"dm_id={dm_id} was not found.")

            match_result = await self.session.execute(
                text("SELECT 1 FROM character_dm_match WHERE dm_id = :dm_id LIMIT 1"),
                {"dm_id": dm_id},
            )
            if match_result.scalar_one_or_none() is not None:
                raise ConflictError("dm is linked to character DM matches.")

            result = await self.session.execute(
                text("DELETE FROM dm WHERE dm_id = :dm_id RETURNING dm_id"),
                {"dm_id": dm_id},
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError(f"dm_id={dm_id} was not found.")

    async def list_dm_store_memberships(
        self, dm_id: int, limit: int, offset: int
    ) -> DmStoreMembershipListResponse:
        await self._assert_dm_exists(dm_id=dm_id)
        items_result = await self.session.execute(
            text(
                """
                SELECT s.store_id, s.name AS store_name
                FROM dm_store_membership AS dsm
                JOIN store AS s ON s.store_id = dsm.store_id
                WHERE dsm.dm_id = :dm_id
                ORDER BY s.name, s.store_id
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {"dm_id": dm_id, "limit": limit, "offset": offset},
        )
        items = [DmStoreMembershipItem(**row) for row in items_result.mappings().all()]
        total_result = await self.session.execute(
            text("SELECT count(*) FROM dm_store_membership WHERE dm_id = :dm_id"),
            {"dm_id": dm_id},
        )
        total = total_result.scalar_one()
        return DmStoreMembershipListResponse(items=items, limit=limit, offset=offset, total=total)

    async def create_dm_store_membership(
        self, dm_id: int, payload: CreateDmStoreMembershipRequest
    ) -> DmStoreMembershipItem:
        async with self.session.begin():
            dm_exists = await self.session.execute(
                text("SELECT 1 FROM dm WHERE dm_id = :dm_id"),
                {"dm_id": dm_id},
            )
            if dm_exists.scalar_one_or_none() is None:
                raise NotFoundError(f"dm_id={dm_id} was not found.")

            store_result = await self.session.execute(
                text("SELECT name FROM store WHERE store_id = :store_id"),
                {"store_id": payload.store_id},
            )
            store_name = store_result.scalar_one_or_none()
            if store_name is None:
                raise NotFoundError(f"store_id={payload.store_id} was not found.")

            existing = await self.session.execute(
                text(
                    """
                    SELECT 1
                    FROM dm_store_membership
                    WHERE dm_id = :dm_id
                      AND store_id = :store_id
                    """
                ),
                {"dm_id": dm_id, "store_id": payload.store_id},
            )
            if existing.scalar_one_or_none() is not None:
                raise ConflictError(
                    f"dm_id={dm_id} already has store_id={payload.store_id} membership."
                )

            await self.session.execute(
                text(
                    """
                    INSERT INTO dm_store_membership (dm_id, store_id)
                    VALUES (:dm_id, :store_id)
                    """
                ),
                {"dm_id": dm_id, "store_id": payload.store_id},
            )
        return DmStoreMembershipItem(store_id=payload.store_id, store_name=store_name)

    async def delete_dm_store_membership(self, dm_id: int, store_id: int) -> None:
        async with self.session.begin():
            dm_exists = await self.session.execute(
                text("SELECT 1 FROM dm WHERE dm_id = :dm_id"),
                {"dm_id": dm_id},
            )
            if dm_exists.scalar_one_or_none() is None:
                raise NotFoundError(f"dm_id={dm_id} was not found.")

            result = await self.session.execute(
                text(
                    """
                    DELETE FROM dm_store_membership
                    WHERE dm_id = :dm_id
                      AND store_id = :store_id
                    RETURNING store_id
                    """
                ),
                {"dm_id": dm_id, "store_id": store_id},
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError(f"dm_id={dm_id} does not have store_id={store_id} membership.")
