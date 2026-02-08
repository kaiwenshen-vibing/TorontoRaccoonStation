from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.script import (
    CreateScriptRequest,
    CreateStoreScriptRequest,
    UpdateScriptRequest,
    UpdateStoreScriptRequest,
)
from app.services.script_service import ScriptService


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
async def test_list_scripts_returns_items_and_total():
    session = FakeSession(
        [
            FakeResult(
                rows=[
                    {"script_id": 1, "name": "Haunted Mansion", "estimated_minutes": 180},
                    {"script_id": 2, "name": "Midnight Train", "estimated_minutes": 240},
                ]
            ),
            FakeResult(scalar=2),
        ]
    )
    service = ScriptService(session=session)

    response = await service.list_scripts(limit=20, offset=0)

    assert response.total == 2
    assert len(response.items) == 2
    assert response.items[0].script_id == 1


@pytest.mark.asyncio
async def test_get_script_not_found():
    session = FakeSession([FakeResult(rows=[])])
    service = ScriptService(session=session)

    with pytest.raises(NotFoundError):
        await service.get_script(script_id=99)


@pytest.mark.asyncio
async def test_create_script_conflict():
    session = FakeSession([])
    session.execute = AsyncMock(
        side_effect=IntegrityError("stmt", {}, Exception("unique")),
    )
    session.begin = lambda: FakeBegin()
    service = ScriptService(session=session)

    with pytest.raises(ConflictError):
        await service.create_script(CreateScriptRequest(name="Dup", estimated_minutes=90))


@pytest.mark.asyncio
async def test_update_script_not_found():
    session = FakeSession([FakeResult(rows=[])])
    service = ScriptService(session=session)

    with pytest.raises(NotFoundError):
        await service.update_script(123, UpdateScriptRequest(name="New"))


@pytest.mark.asyncio
async def test_update_script_conflict():
    session = FakeSession([])
    session.execute = AsyncMock(
        side_effect=IntegrityError("stmt", {}, Exception("unique")),
    )
    session.begin = lambda: FakeBegin()
    service = ScriptService(session=session)

    with pytest.raises(ConflictError):
        await service.update_script(1, UpdateScriptRequest(name="Dup"))


@pytest.mark.asyncio
async def test_delete_script_blocked_by_bookings():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=1),
        ]
    )
    service = ScriptService(session=session)

    with pytest.raises(ConflictError):
        await service.delete_script(script_id=5)


@pytest.mark.asyncio
async def test_delete_script_blocked_by_active_store_script():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=None),
            FakeResult(scalar_or_none=1),
        ]
    )
    service = ScriptService(session=session)

    with pytest.raises(ConflictError):
        await service.delete_script(script_id=5)


@pytest.mark.asyncio
async def test_delete_script_success():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=None),
            FakeResult(scalar_or_none=None),
            FakeResult(),
            FakeResult(),
        ]
    )
    service = ScriptService(session=session)

    await service.delete_script(script_id=5)
    assert len(session.execute_calls) == 5


@pytest.mark.asyncio
async def test_list_store_scripts_returns_items():
    session = FakeSession(
        [
            FakeResult(
                rows=[
                    {
                        "script_id": 1,
                        "name": "Haunted Mansion",
                        "estimated_minutes": 180,
                        "is_active": True,
                    }
                ]
            ),
            FakeResult(scalar=1),
        ]
    )
    service = ScriptService(session=session)

    response = await service.list_store_scripts(store_id=10, limit=20, offset=0)

    assert response.total == 1
    assert response.items[0].is_active is True


@pytest.mark.asyncio
async def test_create_store_script_store_missing():
    session = FakeSession([FakeResult(scalar_or_none=None)])
    service = ScriptService(session=session)

    with pytest.raises(NotFoundError):
        await service.create_store_script(10, CreateStoreScriptRequest(script_id=3))


@pytest.mark.asyncio
async def test_create_store_script_script_missing():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=None),
        ]
    )
    service = ScriptService(session=session)

    with pytest.raises(NotFoundError):
        await service.create_store_script(10, CreateStoreScriptRequest(script_id=3))


@pytest.mark.asyncio
async def test_create_store_script_conflict():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=1),
        ]
    )
    service = ScriptService(session=session)

    with pytest.raises(ConflictError):
        await service.create_store_script(10, CreateStoreScriptRequest(script_id=3))


@pytest.mark.asyncio
async def test_create_store_script_success():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=None),
            FakeResult(),
            FakeResult(
                rows=[
                    {
                        "script_id": 3,
                        "name": "New Script",
                        "estimated_minutes": 120,
                        "is_active": True,
                    }
                ]
            ),
        ]
    )
    service = ScriptService(session=session)

    item = await service.create_store_script(10, CreateStoreScriptRequest(script_id=3))

    assert item.script_id == 3
    assert item.is_active is True


@pytest.mark.asyncio
async def test_update_store_script_not_found():
    session = FakeSession([FakeResult(scalar_or_none=None)])
    service = ScriptService(session=session)

    with pytest.raises(NotFoundError):
        await service.update_store_script(
            10,
            3,
            UpdateStoreScriptRequest(is_active=False),
        )


@pytest.mark.asyncio
async def test_update_store_script_success():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(
                rows=[
                    {
                        "script_id": 3,
                        "name": "New Script",
                        "estimated_minutes": 120,
                        "is_active": False,
                    }
                ]
            ),
        ]
    )
    service = ScriptService(session=session)

    item = await service.update_store_script(
        10,
        3,
        UpdateStoreScriptRequest(is_active=False),
    )

    assert item.is_active is False


@pytest.mark.asyncio
async def test_delete_store_script_blocked_by_booking():
    session = FakeSession([FakeResult(scalar_or_none=1)])
    service = ScriptService(session=session)

    with pytest.raises(ConflictError):
        await service.delete_store_script(10, 3)


@pytest.mark.asyncio
async def test_delete_store_script_not_found():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=None),
            FakeResult(scalar_or_none=None),
        ]
    )
    service = ScriptService(session=session)

    with pytest.raises(NotFoundError):
        await service.delete_store_script(10, 3)


@pytest.mark.asyncio
async def test_delete_store_script_success():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=None),
            FakeResult(scalar_or_none=1),
        ]
    )
    service = ScriptService(session=session)

    await service.delete_store_script(10, 3)
