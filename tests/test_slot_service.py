from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.slot import CreateSlotRequest, UpdateSlotRequest
from app.services.slot_service import SlotService


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


@pytest.mark.asyncio
async def test_list_slots_requires_store():
    session = FakeSession([FakeResult(scalar_or_none=None)])
    service = SlotService(session=session)

    with pytest.raises(NotFoundError):
        await service.list_slots(store_id=1, limit=20, offset=0)


@pytest.mark.asyncio
async def test_list_slots_returns_items():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(
                rows=[
                    {"slot_id": 10, "store_id": 1, "start_at": "2026-03-15T18:00:00Z"}
                ]
            ),
            FakeResult(scalar=1),
        ]
    )
    service = SlotService(session=session)

    response = await service.list_slots(store_id=1, limit=20, offset=0)

    assert response.total == 1
    assert response.items[0].slot_id == 10


@pytest.mark.asyncio
async def test_create_slot_store_missing():
    session = FakeSession([FakeResult(scalar_or_none=None)])
    service = SlotService(session=session)

    with pytest.raises(NotFoundError):
        await service.create_slot(
            store_id=1, payload=CreateSlotRequest(start_at="2026-03-15T18:00:00Z")
        )


@pytest.mark.asyncio
async def test_create_slot_conflict():
    session = FakeSession([FakeResult(scalar_or_none=1)])
    session.execute = AsyncMock(
        side_effect=IntegrityError("stmt", {}, Exception("unique")),
    )
    session.begin = lambda: FakeBegin()
    service = SlotService(session=session)

    with pytest.raises(ConflictError):
        await service.create_slot(
            store_id=1, payload=CreateSlotRequest(start_at="2026-03-15T18:00:00Z")
        )


@pytest.mark.asyncio
async def test_update_slot_not_found():
    session = FakeSession([FakeResult(rows=[])])
    service = SlotService(session=session)

    with pytest.raises(NotFoundError):
        await service.update_slot(
            store_id=1,
            slot_id=10,
            payload=UpdateSlotRequest(start_at="2026-03-15T18:30:00Z"),
        )


@pytest.mark.asyncio
async def test_update_slot_conflict():
    session = FakeSession([])
    session.execute = AsyncMock(
        side_effect=IntegrityError("stmt", {}, Exception("unique")),
    )
    session.begin = lambda: FakeBegin()
    service = SlotService(session=session)

    with pytest.raises(ConflictError):
        await service.update_slot(
            store_id=1,
            slot_id=10,
            payload=UpdateSlotRequest(start_at="2026-03-15T18:30:00Z"),
        )


@pytest.mark.asyncio
async def test_delete_slot_blocked_by_booking():
    session = FakeSession([FakeResult(scalar_or_none=1)])
    service = SlotService(session=session)

    with pytest.raises(ConflictError):
        await service.delete_slot(store_id=1, slot_id=10)


@pytest.mark.asyncio
async def test_delete_slot_not_found():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=None),
            FakeResult(scalar_or_none=None),
        ]
    )
    service = SlotService(session=session)

    with pytest.raises(NotFoundError):
        await service.delete_slot(store_id=1, slot_id=10)


@pytest.mark.asyncio
async def test_delete_slot_success():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=None),
            FakeResult(scalar_or_none=1),
        ]
    )
    service = SlotService(session=session)

    await service.delete_slot(store_id=1, slot_id=10)
