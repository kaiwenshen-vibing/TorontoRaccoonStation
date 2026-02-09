from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.booking import (
    AddBookingClientRequest,
    ConfirmBookingRequest,
    CreateIncompleteBookingRequest,
    UpdateIncompleteBookingRequest,
)
from app.services.booking_service import BookingService


class FakeResult:
    def __init__(self, *, rows=None, scalar=None, scalar_or_none=None) -> None:
        self._rows = rows or []
        self._scalar = scalar
        self._scalar_or_none = scalar_or_none

    def mappings(self) -> "FakeResult":
        return self

    def all(self):
        return self._rows

    def one(self):
        return self._rows[0]

    def one_or_none(self):
        return self._rows[0] if self._rows else None

    def scalar_one(self):
        return self._scalar

    def scalar_one_or_none(self):
        return self._scalar_or_none


class FakeBegin:
    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, results):
        self._results = list(results)
        self.execute_calls = []

    async def execute(self, query, params=None):
        self.execute_calls.append((query, params))
        return self._results.pop(0)

    def begin(self):
        return FakeBegin()


def _booking_row(**overrides):
    base = {
        "booking_id": 1,
        "store_id": 10,
        "script_id": 5,
        "booking_status_id": 1,
        "target_month": "2026-04-01",
        "start_at": None,
        "end_at": None,
        "duration_override_minutes": None,
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_create_incomplete_booking_missing_clients():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(rows=[]),
        ]
    )
    service = BookingService(session=session)

    with pytest.raises(NotFoundError):
        await service.create_incomplete_booking(
            store_id=10,
            payload=CreateIncompleteBookingRequest(
                target_month="2026-04-01",
                client_ids=[1],
                script_id=None,
            ),
        )


@pytest.mark.asyncio
async def test_update_incomplete_booking_clear_script_conflict():
    service = BookingService(session=FakeSession([]))

    with pytest.raises(ConflictError):
        await service.update_incomplete_booking(
            store_id=10,
            booking_id=1,
            payload=UpdateIncompleteBookingRequest(clear_script=True, script_id=2),
        )


@pytest.mark.asyncio
async def test_update_incomplete_booking_not_incomplete():
    session = FakeSession([FakeResult(rows=[])])
    service = BookingService(session=session)

    with pytest.raises(ConflictError):
        await service.update_incomplete_booking(
            store_id=10,
            booking_id=1,
            payload=UpdateIncompleteBookingRequest(target_month="2026-04-01"),
        )


@pytest.mark.asyncio
async def test_confirm_booking_requires_incomplete():
    session = FakeSession([FakeResult(rows=[_booking_row(booking_status_id=2)])])
    service = BookingService(session=session)

    with pytest.raises(ConflictError):
        await service.confirm_booking(
            store_id=10,
            booking_id=1,
            payload=ConfirmBookingRequest(start_at="2026-04-01T10:00:00Z"),
        )


@pytest.mark.asyncio
async def test_confirm_booking_requires_script():
    session = FakeSession([FakeResult(rows=[_booking_row(script_id=None)])])
    service = BookingService(session=session)

    with pytest.raises(ConflictError):
        await service.confirm_booking(
            store_id=10,
            booking_id=1,
            payload=ConfirmBookingRequest(start_at="2026-04-01T10:00:00Z"),
        )


@pytest.mark.asyncio
async def test_confirm_booking_requires_active_script():
    session = FakeSession(
        [
            FakeResult(rows=[_booking_row()]),
            FakeResult(scalar_or_none=None),
        ]
    )
    service = BookingService(session=session)

    with pytest.raises(ConflictError):
        await service.confirm_booking(
            store_id=10,
            booking_id=1,
            payload=ConfirmBookingRequest(start_at="2026-04-01T10:00:00Z"),
        )


@pytest.mark.asyncio
async def test_confirm_booking_requires_clients():
    session = FakeSession(
        [
            FakeResult(rows=[_booking_row()]),
            FakeResult(scalar_or_none=1),
            FakeResult(rows=[]),
        ]
    )
    service = BookingService(session=session)

    with pytest.raises(ConflictError):
        await service.confirm_booking(
            store_id=10,
            booking_id=1,
            payload=ConfirmBookingRequest(start_at="2026-04-01T10:00:00Z"),
        )


@pytest.mark.asyncio
async def test_confirm_booking_requires_bijection():
    session = FakeSession(
        [
            FakeResult(rows=[_booking_row()]),
            FakeResult(scalar_or_none=1),
            FakeResult(rows=[{"client_id": 1}, {"client_id": 2}]),
            FakeResult(rows=[{"character_id": 10}]),
        ]
    )
    service = BookingService(session=session)

    with pytest.raises(ConflictError):
        await service.confirm_booking(
            store_id=10,
            booking_id=1,
            payload=ConfirmBookingRequest(start_at="2026-04-01T10:00:00Z"),
        )


@pytest.mark.asyncio
async def test_confirm_booking_success_prefers_non_conflict_room():
    start_at = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    session = FakeSession(
        [
            FakeResult(rows=[_booking_row()]),
            FakeResult(scalar_or_none=1),
            FakeResult(rows=[{"client_id": 1}]),
            FakeResult(rows=[{"character_id": 10}]),
            FakeResult(rows=[{"character_id": 10, "client_id": 1}]),
            FakeResult(scalar=180),
            FakeResult(rows=[{"store_room_id": 2}, {"store_room_id": 3}]),
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=None),
            FakeResult(scalar_or_none=None),
            FakeResult(scalar_or_none=None),
            FakeResult(rows=[_booking_row(booking_status_id=2, start_at=start_at, end_at=start_at)]),
            FakeResult(rows=[]),
            FakeResult(rows=[]),
        ]
    )
    service = BookingService(session=session)

    item = await service.confirm_booking(
        store_id=10,
        booking_id=1,
        payload=ConfirmBookingRequest(start_at=start_at),
    )

    assert item.booking_status_id == 2


@pytest.mark.asyncio
async def test_add_booking_client_requires_incomplete():
    session = FakeSession([FakeResult(scalar_or_none=2)])
    service = BookingService(session=session)

    with pytest.raises(ConflictError):
        await service.add_booking_client(
            store_id=10,
            booking_id=1,
            payload=AddBookingClientRequest(client_id=1),
        )


@pytest.mark.asyncio
async def test_add_booking_client_conflict():
    session = FakeSession([FakeResult(scalar_or_none=1), FakeResult(scalar_or_none=1)])
    session.execute = AsyncMock(
        side_effect=[
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=1),
            IntegrityError("stmt", {}, Exception("unique")),
        ]
    )
    session.begin = lambda: FakeBegin()
    service = BookingService(session=session)

    with pytest.raises(ConflictError):
        await service.add_booking_client(
            store_id=10,
            booking_id=1,
            payload=AddBookingClientRequest(client_id=1),
        )


@pytest.mark.asyncio
async def test_remove_booking_client_requires_minimum():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar=1),
        ]
    )
    service = BookingService(session=session)

    with pytest.raises(ConflictError):
        await service.remove_booking_client(store_id=10, booking_id=1, client_id=1)
