from datetime import timedelta

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.booking import (
    AddBookingClientRequest,
    BookingItem,
    BookingListResponse,
    ConfirmBookingRequest,
    CreateIncompleteBookingRequest,
    UpdateIncompleteBookingRequest,
)
from app.services.base import BaseService


class BookingService(BaseService):
    async def _assert_store_exists(self, store_id: int) -> None:
        result = await self.session.execute(
            text("SELECT 1 FROM store WHERE store_id = :store_id"),
            {"store_id": store_id},
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundError(f"store_id={store_id} was not found.")

    async def _get_booking_row(self, store_id: int, booking_id: int) -> dict:
        result = await self.session.execute(
            text(
                """
                SELECT booking_id,
                       store_id,
                       script_id,
                       booking_status_id,
                       target_month,
                       start_at,
                       end_at,
                       duration_override_minutes
                FROM booking
                WHERE store_id = :store_id
                  AND booking_id = :booking_id
                """
            ),
            {"store_id": store_id, "booking_id": booking_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise NotFoundError(f"booking_id={booking_id} was not found.")
        return row

    async def _get_booking_client_ids(self, booking_id: int) -> list[int]:
        result = await self.session.execute(
            text(
                """
                SELECT client_id
                FROM booking_client
                WHERE booking_id = :booking_id
                ORDER BY client_id
                """
            ),
            {"booking_id": booking_id},
        )
        return [row["client_id"] for row in result.mappings().all()]

    async def _get_conflicts(self, booking_id: int) -> tuple[bool, int, list[int]]:
        booking_result = await self.session.execute(
            text(
                """
                SELECT booking_id, store_room_id, start_at, end_at, booking_status_id
                FROM booking
                WHERE booking_id = :booking_id
                """
            ),
            {"booking_id": booking_id},
        )
        booking_row = booking_result.mappings().one_or_none()
        if booking_row is None:
            return False, 0, []
        if (
            booking_row["store_room_id"] is None
            or booking_row["start_at"] is None
            or booking_row["end_at"] is None
        ):
            return False, 0, []
        if booking_row["booking_status_id"] not in (2, 4):
            return False, 0, []
        conflict_result = await self.session.execute(
            text(
                """
                SELECT b2.booking_id
                FROM booking AS b2
                WHERE b2.store_room_id = :store_room_id
                  AND b2.booking_id <> :booking_id
                  AND b2.booking_status_id IN (2, 4)
                  AND b2.start_at < :end_at
                  AND b2.end_at > :start_at
                ORDER BY b2.booking_id
                """
            ),
            {
                "store_room_id": booking_row["store_room_id"],
                "booking_id": booking_id,
                "start_at": booking_row["start_at"],
                "end_at": booking_row["end_at"],
            },
        )
        conflict_ids = [row["booking_id"] for row in conflict_result.mappings().all()]
        return bool(conflict_ids), len(conflict_ids), conflict_ids

    async def _build_booking_item(self, row: dict) -> BookingItem:
        client_ids = await self._get_booking_client_ids(booking_id=row["booking_id"])
        has_conflict, conflict_count, conflict_booking_ids = await self._get_conflicts(
            booking_id=row["booking_id"]
        )
        return BookingItem(
            booking_id=row["booking_id"],
            store_id=row["store_id"],
            script_id=row["script_id"],
            booking_status_id=row["booking_status_id"],
            target_month=row["target_month"],
            start_at=row["start_at"],
            end_at=row["end_at"],
            duration_override_minutes=row["duration_override_minutes"],
            client_ids=client_ids,
            has_conflict=has_conflict,
            conflict_count=conflict_count,
            conflict_booking_ids=conflict_booking_ids,
        )

    async def create_incomplete_booking(
        self,
        store_id: int,
        payload: CreateIncompleteBookingRequest,
    ) -> BookingItem:
        await self._assert_store_exists(store_id=store_id)
        if payload.script_id is not None:
            script_result = await self.session.execute(
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
            if script_result.scalar_one_or_none() is None:
                raise NotFoundError(
                    f"script_id={payload.script_id} is not available for store_id={store_id}."
                )

        client_result = await self.session.execute(
            text(
                """
                SELECT client_id
                FROM client
                WHERE client_id = ANY(:client_ids)
                """
            ),
            {"client_ids": payload.client_ids},
        )
        found_client_ids = {row["client_id"] for row in client_result.mappings().all()}
        missing_clients = [cid for cid in payload.client_ids if cid not in found_client_ids]
        if missing_clients:
            raise NotFoundError(f"client_ids not found: {missing_clients}")

        async with self.session.begin():
            booking_result = await self.session.execute(
                text(
                    """
                    INSERT INTO booking (store_id, script_id, booking_status_id, target_month)
                    VALUES (:store_id, :script_id, 1, :target_month)
                    RETURNING booking_id,
                              store_id,
                              script_id,
                              booking_status_id,
                              target_month,
                              start_at,
                              end_at,
                              duration_override_minutes
                    """
                ),
                {
                    "store_id": store_id,
                    "script_id": payload.script_id,
                    "target_month": payload.target_month,
                },
            )
            booking_row = booking_result.mappings().one()

            await self.session.execute(
                text(
                    """
                    INSERT INTO booking_client (booking_id, client_id)
                    SELECT :booking_id, unnest(:client_ids)
                    """
                ),
                {"booking_id": booking_row["booking_id"], "client_ids": payload.client_ids},
            )
        return await self._build_booking_item(booking_row)

    async def list_bookings(
        self,
        store_id: int,
        *,
        booking_status_id: int | None,
        target_month: str | None,
        has_conflict: bool | None,
        limit: int,
        offset: int,
    ) -> BookingListResponse:
        await self._assert_store_exists(store_id=store_id)
        conditions = ["b.store_id = :store_id"]
        params: dict[str, object] = {"store_id": store_id, "limit": limit, "offset": offset}
        if booking_status_id is not None:
            conditions.append("b.booking_status_id = :booking_status_id")
            params["booking_status_id"] = booking_status_id
        if target_month is not None:
            conditions.append("b.target_month = :target_month")
            params["target_month"] = target_month
        if has_conflict is not None:
            conflict_clause = """
                EXISTS (
                    SELECT 1
                    FROM booking AS b2
                    WHERE b2.store_room_id = b.store_room_id
                      AND b2.booking_id <> b.booking_id
                      AND b2.booking_status_id IN (2, 4)
                      AND b.booking_status_id IN (2, 4)
                      AND b.start_at IS NOT NULL
                      AND b.end_at IS NOT NULL
                      AND b2.start_at < b.end_at
                      AND b2.end_at > b.start_at
                )
            """
            conditions.append(conflict_clause if has_conflict else f"NOT {conflict_clause}")

        where_clause = " AND ".join(conditions)
        items_result = await self.session.execute(
            text(
                f"""
                SELECT b.booking_id,
                       b.store_id,
                       b.script_id,
                       b.booking_status_id,
                       b.target_month,
                       b.start_at,
                       b.end_at,
                       b.duration_override_minutes
                FROM booking AS b
                WHERE {where_clause}
                ORDER BY b.updated_at DESC, b.booking_id DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            params,
        )
        rows = items_result.mappings().all()
        if not rows:
            total_result = await self.session.execute(
                text(f"SELECT count(*) FROM booking AS b WHERE {where_clause}"),
                {k: v for k, v in params.items() if k not in {"limit", "offset"}},
            )
            total = total_result.scalar_one()
            return BookingListResponse(items=[], limit=limit, offset=offset, total=total)

        booking_ids = [row["booking_id"] for row in rows]
        client_result = await self.session.execute(
            text(
                """
                SELECT booking_id, client_id
                FROM booking_client
                WHERE booking_id = ANY(:booking_ids)
                ORDER BY client_id
                """
            ),
            {"booking_ids": booking_ids},
        )
        client_map: dict[int, list[int]] = {bid: [] for bid in booking_ids}
        for row in client_result.mappings().all():
            client_map[row["booking_id"]].append(row["client_id"])

        items: list[BookingItem] = []
        for row in rows:
            has_conflict_value, conflict_count, conflict_booking_ids = await self._get_conflicts(
                booking_id=row["booking_id"]
            )
            items.append(
                BookingItem(
                    booking_id=row["booking_id"],
                    store_id=row["store_id"],
                    script_id=row["script_id"],
                    booking_status_id=row["booking_status_id"],
                    target_month=row["target_month"],
                    start_at=row["start_at"],
                    end_at=row["end_at"],
                    duration_override_minutes=row["duration_override_minutes"],
                    client_ids=client_map.get(row["booking_id"], []),
                    has_conflict=has_conflict_value,
                    conflict_count=conflict_count,
                    conflict_booking_ids=conflict_booking_ids,
                )
            )

        total_result = await self.session.execute(
            text(f"SELECT count(*) FROM booking AS b WHERE {where_clause}"),
            {k: v for k, v in params.items() if k not in {"limit", "offset"}},
        )
        total = total_result.scalar_one()
        return BookingListResponse(items=items, limit=limit, offset=offset, total=total)

    async def get_booking(self, store_id: int, booking_id: int) -> BookingItem:
        row = await self._get_booking_row(store_id=store_id, booking_id=booking_id)
        return await self._build_booking_item(row)

    async def update_incomplete_booking(
        self,
        store_id: int,
        booking_id: int,
        payload: UpdateIncompleteBookingRequest,
    ) -> BookingItem:
        if payload.clear_script and payload.script_id is not None:
            raise ConflictError("clear_script cannot be combined with script_id.")

        if payload.script_id is not None:
            script_result = await self.session.execute(
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
            if script_result.scalar_one_or_none() is None:
                raise NotFoundError(
                    f"script_id={payload.script_id} is not available for store_id={store_id}."
                )

        values = {"store_id": store_id, "booking_id": booking_id}
        updates = []
        if payload.target_month is not None:
            updates.append("target_month = :target_month")
            values["target_month"] = payload.target_month
        if payload.clear_script:
            updates.append("script_id = NULL")
        elif payload.script_id is not None:
            updates.append("script_id = :script_id")
            values["script_id"] = payload.script_id
        updates.append("updated_at = now()")
        query = f"""
            UPDATE booking
            SET {", ".join(updates)}
            WHERE store_id = :store_id
              AND booking_id = :booking_id
              AND booking_status_id = 1
            RETURNING booking_id,
                      store_id,
                      script_id,
                      booking_status_id,
                      target_month,
                      start_at,
                      end_at,
                      duration_override_minutes
        """
        async with self.session.begin():
            result = await self.session.execute(text(query), values)
            row = result.mappings().one_or_none()
            if row is None:
                raise ConflictError("booking is not incomplete or was not found.")
        return await self._build_booking_item(row)

    async def confirm_booking(
        self,
        store_id: int,
        booking_id: int,
        payload: ConfirmBookingRequest,
    ) -> BookingItem:
        async with self.session.begin():
            booking_row = await self._get_booking_row(store_id=store_id, booking_id=booking_id)
            if booking_row["booking_status_id"] != 1:
                raise ConflictError("booking must be incomplete to confirm.")
            if booking_row["script_id"] is None:
                raise ConflictError("booking must have script_id to confirm.")

            script_active_result = await self.session.execute(
                text(
                    """
                    SELECT 1
                    FROM store_script
                    WHERE store_id = :store_id
                      AND script_id = :script_id
                      AND is_active = true
                    """
                ),
                {"store_id": store_id, "script_id": booking_row["script_id"]},
            )
            if script_active_result.scalar_one_or_none() is None:
                raise ConflictError("script is not active for this store.")

            client_result = await self.session.execute(
                text(
                    """
                    SELECT client_id
                    FROM booking_client
                    WHERE booking_id = :booking_id
                    """
                ),
                {"booking_id": booking_id},
            )
            booking_client_ids = [row["client_id"] for row in client_result.mappings().all()]
            if not booking_client_ids:
                raise ConflictError("booking must have at least one client.")

            character_result = await self.session.execute(
                text(
                    """
                    SELECT character_id
                    FROM script_character
                    WHERE script_id = :script_id
                      AND is_dm = false
                      AND is_active = true
                    """
                ),
                {"script_id": booking_row["script_id"]},
            )
            character_ids = [row["character_id"] for row in character_result.mappings().all()]
            if len(character_ids) != len(booking_client_ids):
                raise ConflictError("booking clients must match non-DM character count.")

            match_result = await self.session.execute(
                text(
                    """
                    SELECT character_id, client_id
                    FROM character_client_match
                    WHERE booking_id = :booking_id
                    """
                ),
                {"booking_id": booking_id},
            )
            match_rows = match_result.mappings().all()
            match_character_ids = {row["character_id"] for row in match_rows}
            match_client_ids = {row["client_id"] for row in match_rows}
            if (
                len(match_rows) != len(character_ids)
                or match_character_ids != set(character_ids)
                or match_client_ids != set(booking_client_ids)
            ):
                raise ConflictError("character/client matches must be a strict bijection.")

            duration_result = await self.session.execute(
                text(
                    """
                    SELECT estimated_minutes
                    FROM script
                    WHERE script_id = :script_id
                    """
                ),
                {"script_id": booking_row["script_id"]},
            )
            estimated_minutes = duration_result.scalar_one()
            effective_minutes = (
                booking_row["duration_override_minutes"] or estimated_minutes
            )
            end_at = payload.start_at + timedelta(minutes=effective_minutes)

            room_result = await self.session.execute(
                text(
                    """
                    SELECT store_room_id
                    FROM store_room
                    WHERE store_id = :store_id
                      AND is_active = true
                    ORDER BY store_room_id
                    """
                ),
                {"store_id": store_id},
            )
            room_ids = [row["store_room_id"] for row in room_result.mappings().all()]
            if not room_ids:
                raise ConflictError("store has no active rooms.")

            async def has_conflict(room_id: int) -> bool:
                conflict_check = await self.session.execute(
                    text(
                        """
                        SELECT 1
                        FROM booking AS b2
                        WHERE b2.store_room_id = :store_room_id
                          AND b2.booking_status_id IN (2, 4)
                          AND b2.start_at < :end_at
                          AND b2.end_at > :start_at
                        LIMIT 1
                        """
                    ),
                    {"store_room_id": room_id, "start_at": payload.start_at, "end_at": end_at},
                )
                return conflict_check.scalar_one_or_none() is not None

            selected_room_id = None
            preferred_id = payload.preferred_room_id
            if preferred_id is not None:
                room_exists = await self.session.execute(
                    text(
                        """
                        SELECT 1
                        FROM store_room
                        WHERE store_id = :store_id
                          AND store_room_id = :store_room_id
                          AND is_active = true
                        """
                    ),
                    {"store_id": store_id, "store_room_id": preferred_id},
                )
                if room_exists.scalar_one_or_none() is None:
                    raise NotFoundError(f"store_room_id={preferred_id} was not found.")
                if not await has_conflict(preferred_id):
                    selected_room_id = preferred_id

            if selected_room_id is None:
                for room_id in room_ids:
                    if not await has_conflict(room_id):
                        selected_room_id = room_id
                        break

            if selected_room_id is None:
                selected_room_id = preferred_id or room_ids[0]

            slot_result = await self.session.execute(
                text(
                    """
                    SELECT slot_id
                    FROM slot
                    WHERE store_id = :store_id
                      AND start_at = :start_at
                    """
                ),
                {"store_id": store_id, "start_at": payload.start_at},
            )
            slot_id = slot_result.scalar_one_or_none()
            if slot_id is None:
                slot_insert = await self.session.execute(
                    text(
                        """
                        INSERT INTO slot (store_id, start_at)
                        VALUES (:store_id, :start_at)
                        RETURNING slot_id
                        """
                    ),
                    {"store_id": store_id, "start_at": payload.start_at},
                )
                slot_id = slot_insert.scalar_one()

            update_result = await self.session.execute(
                text(
                    """
                    UPDATE booking
                    SET booking_status_id = 2,
                        slot_id = :slot_id,
                        store_room_id = :store_room_id,
                        start_at = :start_at,
                        updated_at = now()
                    WHERE booking_id = :booking_id
                    RETURNING booking_id,
                              store_id,
                              script_id,
                              booking_status_id,
                              target_month,
                              start_at,
                              end_at,
                              duration_override_minutes
                    """
                ),
                {
                    "booking_id": booking_id,
                    "slot_id": slot_id,
                    "store_room_id": selected_room_id,
                    "start_at": payload.start_at,
                },
            )
            updated_row = update_result.mappings().one()
        return await self._build_booking_item(updated_row)

    async def cancel_booking(self, store_id: int, booking_id: int) -> BookingItem:
        async with self.session.begin():
            result = await self.session.execute(
                text(
                    """
                    UPDATE booking
                    SET booking_status_id = 3,
                        updated_at = now()
                    WHERE store_id = :store_id
                      AND booking_id = :booking_id
                    RETURNING booking_id,
                              store_id,
                              script_id,
                              booking_status_id,
                              target_month,
                              start_at,
                              end_at,
                              duration_override_minutes
                    """
                ),
                {"store_id": store_id, "booking_id": booking_id},
            )
            row = result.mappings().one_or_none()
            if row is None:
                raise NotFoundError(f"booking_id={booking_id} was not found.")
        return await self._build_booking_item(row)

    async def complete_booking(self, store_id: int, booking_id: int) -> BookingItem:
        async with self.session.begin():
            status_result = await self.session.execute(
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
            current_status = status_result.scalar_one_or_none()
            if current_status is None:
                raise NotFoundError(f"booking_id={booking_id} was not found.")
            if current_status != 2:
                raise ConflictError("booking must be scheduled to complete.")

            result = await self.session.execute(
                text(
                    """
                    UPDATE booking
                    SET booking_status_id = 4,
                        updated_at = now()
                    WHERE store_id = :store_id
                      AND booking_id = :booking_id
                    RETURNING booking_id,
                              store_id,
                              script_id,
                              booking_status_id,
                              target_month,
                              start_at,
                              end_at,
                              duration_override_minutes
                    """
                ),
                {"store_id": store_id, "booking_id": booking_id},
            )
            row = result.mappings().one()
        return await self._build_booking_item(row)

    async def add_booking_client(
        self,
        store_id: int,
        booking_id: int,
        payload: AddBookingClientRequest,
    ) -> BookingItem:
        async with self.session.begin():
            status_result = await self.session.execute(
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
            status_id = status_result.scalar_one_or_none()
            if status_id is None:
                raise NotFoundError(f"booking_id={booking_id} was not found.")
            if status_id != 1:
                raise ConflictError("clients can only be modified for incomplete bookings.")

            client_result = await self.session.execute(
                text("SELECT 1 FROM client WHERE client_id = :client_id"),
                {"client_id": payload.client_id},
            )
            if client_result.scalar_one_or_none() is None:
                raise NotFoundError(f"client_id={payload.client_id} was not found.")

            try:
                await self.session.execute(
                    text(
                        """
                        INSERT INTO booking_client (booking_id, client_id)
                        VALUES (:booking_id, :client_id)
                        """
                    ),
                    {"booking_id": booking_id, "client_id": payload.client_id},
                )
            except IntegrityError as exc:
                raise ConflictError("client already linked to booking.") from exc

            booking_row = await self._get_booking_row(store_id=store_id, booking_id=booking_id)
        return await self._build_booking_item(booking_row)

    async def remove_booking_client(
        self,
        store_id: int,
        booking_id: int,
        client_id: int,
    ) -> BookingItem:
        async with self.session.begin():
            status_result = await self.session.execute(
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
            status_id = status_result.scalar_one_or_none()
            if status_id is None:
                raise NotFoundError(f"booking_id={booking_id} was not found.")
            if status_id != 1:
                raise ConflictError("clients can only be modified for incomplete bookings.")

            count_result = await self.session.execute(
                text(
                    """
                    SELECT count(*) FROM booking_client WHERE booking_id = :booking_id
                    """
                ),
                {"booking_id": booking_id},
            )
            if count_result.scalar_one() <= 1:
                raise ConflictError("booking must retain at least one client.")

            delete_result = await self.session.execute(
                text(
                    """
                    DELETE FROM booking_client
                    WHERE booking_id = :booking_id
                      AND client_id = :client_id
                    RETURNING booking_client_id
                    """
                ),
                {"booking_id": booking_id, "client_id": client_id},
            )
            if delete_result.scalar_one_or_none() is None:
                raise NotFoundError(
                    f"booking_id={booking_id} does not have client_id={client_id}."
                )

            booking_row = await self._get_booking_row(store_id=store_id, booking_id=booking_id)
        return await self._build_booking_item(booking_row)
