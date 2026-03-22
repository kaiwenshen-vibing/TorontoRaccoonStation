from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.client import ClientItem, ClientListResponse, CreateClientRequest, UpdateClientRequest
from app.services.base import BaseService


class ClientService(BaseService):
    async def list_clients(self, limit: int, offset: int) -> ClientListResponse:
        items_result = await self.session.execute(
            text(
                """
                SELECT client_id, display_name, phone, pic_storage_key
                FROM client
                ORDER BY updated_at DESC, client_id DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {"limit": limit, "offset": offset},
        )
        items = [ClientItem(**row) for row in items_result.mappings().all()]
        total_result = await self.session.execute(text("SELECT count(*) FROM client"))
        total = total_result.scalar_one()
        return ClientListResponse(items=items, limit=limit, offset=offset, total=total)

    async def get_client(self, client_id: int) -> ClientItem:
        result = await self.session.execute(
            text(
                """
                SELECT client_id, display_name, phone, pic_storage_key
                FROM client
                WHERE client_id = :client_id
                """
            ),
            {"client_id": client_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise NotFoundError(f"client_id={client_id} was not found.")
        return ClientItem(**row)

    async def create_client(self, payload: CreateClientRequest) -> ClientItem:
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    text(
                        """
                        INSERT INTO client (display_name, phone, pic_storage_key)
                        VALUES (:display_name, :phone, :pic_storage_key)
                        RETURNING client_id, display_name, phone, pic_storage_key
                        """
                    ),
                    payload.model_dump(),
                )
                row = result.mappings().one()
        except IntegrityError as exc:
            raise ConflictError("client could not be created.") from exc
        return ClientItem(**row)

    async def update_client(self, client_id: int, payload: UpdateClientRequest) -> ClientItem:
        values = {"client_id": client_id}
        updates = []
        if "display_name" in payload.model_fields_set:
            updates.append("display_name = :display_name")
            values["display_name"] = payload.display_name
        if "phone" in payload.model_fields_set:
            updates.append("phone = :phone")
            values["phone"] = payload.phone
        if "pic_storage_key" in payload.model_fields_set:
            updates.append("pic_storage_key = :pic_storage_key")
            values["pic_storage_key"] = payload.pic_storage_key
        updates.append("updated_at = now()")
        query = f"""
            UPDATE client
            SET {", ".join(updates)}
            WHERE client_id = :client_id
            RETURNING client_id, display_name, phone, pic_storage_key
        """
        async with self.session.begin():
            result = await self.session.execute(text(query), values)
            row = result.mappings().one_or_none()
            if row is None:
                raise NotFoundError(f"client_id={client_id} was not found.")
        return ClientItem(**row)

    async def delete_client(self, client_id: int) -> None:
        async with self.session.begin():
            exists_result = await self.session.execute(
                text("SELECT 1 FROM client WHERE client_id = :client_id"),
                {"client_id": client_id},
            )
            if exists_result.scalar_one_or_none() is None:
                raise NotFoundError(f"client_id={client_id} was not found.")

            dependency_checks = (
                ("booking_client", "client is linked to bookings."),
                ("character_client_match", "client is linked to character matches."),
            )
            for table_name, message in dependency_checks:
                result = await self.session.execute(
                    text(f"SELECT 1 FROM {table_name} WHERE client_id = :client_id LIMIT 1"),
                    {"client_id": client_id},
                )
                if result.scalar_one_or_none() is not None:
                    raise ConflictError(message)

            result = await self.session.execute(
                text("DELETE FROM client WHERE client_id = :client_id RETURNING client_id"),
                {"client_id": client_id},
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError(f"client_id={client_id} was not found.")
