from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.booking import CreateCharacterDmMatchRequest, UpdateCharacterDmMatchRequest
from app.services.character_dm_match_service import CharacterDmMatchService


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
async def test_create_match_requires_incomplete():
    session = FakeSession([FakeResult(scalar_or_none=2)])
    service = CharacterDmMatchService(session=session)

    with pytest.raises(ConflictError):
        await service.create_match(
            store_id=1,
            booking_id=10,
            payload=CreateCharacterDmMatchRequest(dm_id=1),
        )


@pytest.mark.asyncio
async def test_create_match_conflict():
    session = FakeSession([FakeResult(scalar_or_none=1)])
    session.execute = AsyncMock(
        side_effect=IntegrityError("stmt", {}, Exception("unique")),
    )
    session.begin = lambda: FakeBegin()
    service = CharacterDmMatchService(session=session)

    with pytest.raises(ConflictError):
        await service.create_match(
            store_id=1,
            booking_id=10,
            payload=CreateCharacterDmMatchRequest(dm_id=1),
        )


@pytest.mark.asyncio
async def test_update_match_not_found():
    session = FakeSession([FakeResult(scalar_or_none=1), FakeResult(rows=[])])
    service = CharacterDmMatchService(session=session)

    with pytest.raises(NotFoundError):
        await service.update_match(
            store_id=1,
            booking_id=10,
            match_id=5,
            payload=UpdateCharacterDmMatchRequest(dm_id=2),
        )


@pytest.mark.asyncio
async def test_delete_match_not_found():
    session = FakeSession([FakeResult(scalar_or_none=1), FakeResult(scalar_or_none=None)])
    service = CharacterDmMatchService(session=session)

    with pytest.raises(NotFoundError):
        await service.delete_match(store_id=1, booking_id=10, match_id=5)
