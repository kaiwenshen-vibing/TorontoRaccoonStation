import pytest

from app.core.errors import ConflictError, NotFoundError
from app.schemas.store import CreateStoreRequest, UpdateStoreRequest
from app.services.store_service import StoreService


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
async def test_list_stores_filters_by_allowed_store_ids():
    session = FakeSession(
        [
            FakeResult(rows=[{"store_id": 2, "name": "Store 2", "pic_storage_key": "stores/2.webp"}]),
            FakeResult(scalar=1),
        ]
    )
    service = StoreService(session=session)

    response = await service.list_stores({2, 5}, limit=20, offset=0)

    assert response.total == 1
    assert response.items[0].store_id == 2


@pytest.mark.asyncio
async def test_create_store_returns_item():
    session = FakeSession(
        [FakeResult(rows=[{"store_id": 3, "name": "New", "pic_storage_key": "stores/3.webp"}])]
    )
    service = StoreService(session=session)

    item = await service.create_store(CreateStoreRequest(name="New", pic_storage_key="stores/3.webp"))

    assert item.pic_storage_key == "stores/3.webp"


@pytest.mark.asyncio
async def test_update_store_can_clear_pic_storage_key():
    session = FakeSession(
        [FakeResult(rows=[{"store_id": 3, "name": "New", "pic_storage_key": None}])]
    )
    service = StoreService(session=session)

    item = await service.update_store(3, UpdateStoreRequest(pic_storage_key=None))

    assert item.pic_storage_key is None


@pytest.mark.asyncio
async def test_delete_store_not_found():
    session = FakeSession([FakeResult(scalar_or_none=None)])
    service = StoreService(session=session)

    with pytest.raises(NotFoundError):
        await service.delete_store(4)


@pytest.mark.asyncio
async def test_delete_store_blocked_by_rooms():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=1),
        ]
    )
    service = StoreService(session=session)

    with pytest.raises(ConflictError):
        await service.delete_store(4)
