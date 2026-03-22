import pytest

from app.core.errors import ConflictError, NotFoundError
from app.schemas.client import CreateClientRequest, UpdateClientRequest
from app.services.client_service import ClientService


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
async def test_list_clients_returns_items():
    session = FakeSession(
        [
            FakeResult(
                rows=[
                    {
                        "client_id": 1,
                        "display_name": "Alex",
                        "phone": "555",
                        "pic_storage_key": "clients/1.webp",
                    }
                ]
            ),
            FakeResult(scalar=1),
        ]
    )
    service = ClientService(session=session)

    response = await service.list_clients(limit=20, offset=0)

    assert response.items[0].pic_storage_key == "clients/1.webp"


@pytest.mark.asyncio
async def test_create_client_returns_item():
    session = FakeSession(
        [
            FakeResult(
                rows=[
                    {
                        "client_id": 1,
                        "display_name": "Alex",
                        "phone": "555",
                        "pic_storage_key": "clients/1.webp",
                    }
                ]
            )
        ]
    )
    service = ClientService(session=session)

    item = await service.create_client(
        CreateClientRequest(display_name="Alex", phone="555", pic_storage_key="clients/1.webp")
    )

    assert item.client_id == 1


@pytest.mark.asyncio
async def test_update_client_can_clear_pic_storage_key():
    session = FakeSession(
        [FakeResult(rows=[{"client_id": 1, "display_name": "Alex", "phone": None, "pic_storage_key": None}])]
    )
    service = ClientService(session=session)

    item = await service.update_client(1, UpdateClientRequest(pic_storage_key=None))

    assert item.pic_storage_key is None


@pytest.mark.asyncio
async def test_delete_client_blocked_by_booking_link():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(scalar_or_none=1),
        ]
    )
    service = ClientService(session=session)

    with pytest.raises(ConflictError):
        await service.delete_client(1)


@pytest.mark.asyncio
async def test_get_client_not_found():
    session = FakeSession([FakeResult(rows=[])])
    service = ClientService(session=session)

    with pytest.raises(NotFoundError):
        await service.get_client(1)
