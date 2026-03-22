import pytest

from app.core.errors import ConflictError, NotFoundError
from app.schemas.dm import CreateDmRequest, CreateDmStoreMembershipRequest, UpdateDmRequest
from app.services.dm_service import DmService


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
async def test_list_dms_returns_items():
    session = FakeSession(
        [
            FakeResult(
                rows=[
                    {
                        "dm_id": 1,
                        "display_name": "DM Ava",
                        "is_active": True,
                        "pic_storage_key": "dms/1.webp",
                    }
                ]
            ),
            FakeResult(scalar=1),
        ]
    )
    service = DmService(session=session)

    response = await service.list_dms(limit=20, offset=0)

    assert response.items[0].pic_storage_key == "dms/1.webp"


@pytest.mark.asyncio
async def test_create_dm_returns_item():
    session = FakeSession(
        [
            FakeResult(
                rows=[
                    {
                        "dm_id": 1,
                        "display_name": "DM Ava",
                        "is_active": True,
                        "pic_storage_key": "dms/1.webp",
                    }
                ]
            )
        ]
    )
    service = DmService(session=session)

    item = await service.create_dm(
        CreateDmRequest(display_name="DM Ava", pic_storage_key="dms/1.webp")
    )

    assert item.dm_id == 1


@pytest.mark.asyncio
async def test_update_dm_can_clear_pic_storage_key():
    session = FakeSession(
        [FakeResult(rows=[{"dm_id": 1, "display_name": "DM Ava", "is_active": True, "pic_storage_key": None}])]
    )
    service = DmService(session=session)

    item = await service.update_dm(1, UpdateDmRequest(pic_storage_key=None))

    assert item.pic_storage_key is None


@pytest.mark.asyncio
async def test_delete_dm_blocked_by_match():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=1),
        ]
    )
    service = DmService(session=session)

    with pytest.raises(ConflictError):
        await service.delete_dm(1)


@pytest.mark.asyncio
async def test_list_dm_store_memberships_requires_dm():
    session = FakeSession([FakeResult(scalar_or_none=None)])
    service = DmService(session=session)

    with pytest.raises(NotFoundError):
        await service.list_dm_store_memberships(1, limit=20, offset=0)


@pytest.mark.asyncio
async def test_create_dm_store_membership_returns_item():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none="Store A"),
            FakeResult(scalar_or_none=None),
            FakeResult(),
        ]
    )
    service = DmService(session=session)

    item = await service.create_dm_store_membership(
        1,
        CreateDmStoreMembershipRequest(store_id=10),
    )

    assert item.store_id == 10
    assert item.store_name == "Store A"


@pytest.mark.asyncio
async def test_delete_dm_store_membership_not_found():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=None),
        ]
    )
    service = DmService(session=session)

    with pytest.raises(NotFoundError):
        await service.delete_dm_store_membership(1, 10)
