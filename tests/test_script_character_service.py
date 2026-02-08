from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.script_character import (
    CreateScriptCharacterRequest,
    UpdateScriptCharacterRequest,
)
from app.services.script_character_service import ScriptCharacterService


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
async def test_list_script_characters_requires_script():
    session = FakeSession([FakeResult(scalar_or_none=None)])
    service = ScriptCharacterService(session=session)

    with pytest.raises(NotFoundError):
        await service.list_script_characters(script_id=1, limit=20, offset=0)


@pytest.mark.asyncio
async def test_list_script_characters_returns_items():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(
                rows=[
                    {
                        "character_id": 1,
                        "script_id": 2,
                        "character_name": "Host",
                        "is_dm": True,
                        "is_active": True,
                    }
                ]
            ),
            FakeResult(scalar=1),
        ]
    )
    service = ScriptCharacterService(session=session)

    response = await service.list_script_characters(script_id=2, limit=20, offset=0)

    assert response.total == 1
    assert response.items[0].character_name == "Host"


@pytest.mark.asyncio
async def test_create_script_character_script_missing():
    session = FakeSession([FakeResult(scalar_or_none=None)])
    service = ScriptCharacterService(session=session)

    with pytest.raises(NotFoundError):
        await service.create_script_character(
            script_id=2,
            payload=CreateScriptCharacterRequest(character_name="Host"),
        )


@pytest.mark.asyncio
async def test_create_script_character_conflict():
    session = FakeSession([FakeResult(scalar_or_none=1)])
    session.execute = AsyncMock(
        side_effect=IntegrityError("stmt", {}, Exception("unique")),
    )
    session.begin = lambda: FakeBegin()
    service = ScriptCharacterService(session=session)

    with pytest.raises(ConflictError):
        await service.create_script_character(
            script_id=2,
            payload=CreateScriptCharacterRequest(character_name="Host"),
        )


@pytest.mark.asyncio
async def test_get_script_character_not_found():
    session = FakeSession([FakeResult(rows=[])])
    service = ScriptCharacterService(session=session)

    with pytest.raises(NotFoundError):
        await service.get_script_character(script_id=2, character_id=10)


@pytest.mark.asyncio
async def test_update_script_character_not_found():
    session = FakeSession([FakeResult(rows=[])])
    service = ScriptCharacterService(session=session)

    with pytest.raises(NotFoundError):
        await service.update_script_character(
            script_id=2,
            character_id=10,
            payload=UpdateScriptCharacterRequest(character_name="New"),
        )


@pytest.mark.asyncio
async def test_update_script_character_conflict():
    session = FakeSession([])
    session.execute = AsyncMock(
        side_effect=IntegrityError("stmt", {}, Exception("unique")),
    )
    session.begin = lambda: FakeBegin()
    service = ScriptCharacterService(session=session)

    with pytest.raises(ConflictError):
        await service.update_script_character(
            script_id=2,
            character_id=10,
            payload=UpdateScriptCharacterRequest(character_name="New"),
        )


@pytest.mark.asyncio
async def test_delete_script_character_not_found():
    session = FakeSession([FakeResult(scalar_or_none=None)])
    service = ScriptCharacterService(session=session)

    with pytest.raises(NotFoundError):
        await service.delete_script_character(script_id=2, character_id=10)


@pytest.mark.asyncio
async def test_delete_script_character_success():
    session = FakeSession([FakeResult(scalar_or_none=1)])
    service = ScriptCharacterService(session=session)

    await service.delete_script_character(script_id=2, character_id=10)
