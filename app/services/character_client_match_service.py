from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.booking import (
    CharacterClientMatchItem,
    CreateCharacterClientMatchRequest,
    UpdateCharacterClientMatchRequest,
)
from app.services.base import BaseService


class CharacterClientMatchService(BaseService):
    async def _assert_booking(self, store_id: int, booking_id: int) -> int:
        result = await self.session.execute(
            text(
                """
                SELECT booking_status_id
                FROM booking
                WHERE store_id = :store_id
                  AND booking_id = :booking_id
                """
            ),
            {"store_id": store_id, "booking_id": booking_id},
        )
        status_id = result.scalar_one_or_none()
        if status_id is None:
            raise NotFoundError(f"booking_id={booking_id} was not found.")
        return status_id

    async def create_match(
        self,
        store_id: int,
        booking_id: int,
        payload: CreateCharacterClientMatchRequest,
    ) -> CharacterClientMatchItem:
        status_id = await self._assert_booking(store_id=store_id, booking_id=booking_id)
        if status_id != 1:
            raise ConflictError("matches can only be modified for incomplete bookings.")
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    text(
                        """
                        INSERT INTO character_client_match (booking_id, character_id, client_id)
                        VALUES (:booking_id, :character_id, :client_id)
                        RETURNING character_client_match_id,
                                  booking_id,
                                  character_id,
                                  client_id
                        """
                    ),
                    {
                        "booking_id": booking_id,
                        "character_id": payload.character_id,
                        "client_id": payload.client_id,
                    },
                )
                row = result.mappings().one()
        except IntegrityError as exc:
            raise ConflictError("character/client match violates constraints.") from exc
        return CharacterClientMatchItem(**row)

    async def update_match(
        self,
        store_id: int,
        booking_id: int,
        match_id: int,
        payload: UpdateCharacterClientMatchRequest,
    ) -> CharacterClientMatchItem:
        status_id = await self._assert_booking(store_id=store_id, booking_id=booking_id)
        if status_id != 1:
            raise ConflictError("matches can only be modified for incomplete bookings.")

        values = {"booking_id": booking_id, "match_id": match_id}
        updates = []
        if payload.character_id is not None:
            updates.append("character_id = :character_id")
            values["character_id"] = payload.character_id
        if payload.client_id is not None:
            updates.append("client_id = :client_id")
            values["client_id"] = payload.client_id
        updates.append("updated_at = now()")
        query = f"""
            UPDATE character_client_match
            SET {", ".join(updates)}
            WHERE booking_id = :booking_id
              AND character_client_match_id = :match_id
            RETURNING character_client_match_id,
                      booking_id,
                      character_id,
                      client_id
        """
        try:
            async with self.session.begin():
                result = await self.session.execute(text(query), values)
                row = result.mappings().one_or_none()
                if row is None:
                    raise NotFoundError(
                        f"booking_id={booking_id} does not have match_id={match_id}."
                    )
        except IntegrityError as exc:
            raise ConflictError("character/client match violates constraints.") from exc
        return CharacterClientMatchItem(**row)

    async def delete_match(self, store_id: int, booking_id: int, match_id: int) -> None:
        status_id = await self._assert_booking(store_id=store_id, booking_id=booking_id)
        if status_id != 1:
            raise ConflictError("matches can only be modified for incomplete bookings.")

        async with self.session.begin():
            result = await self.session.execute(
                text(
                    """
                    DELETE FROM character_client_match
                    WHERE booking_id = :booking_id
                      AND character_client_match_id = :match_id
                    RETURNING character_client_match_id
                    """
                ),
                {"booking_id": booking_id, "match_id": match_id},
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError(
                    f"booking_id={booking_id} does not have match_id={match_id}."
                )
