import pytest

from app.core.errors import NotFoundError
from app.schemas.room import CreateRoomRequest, UpdateRoomRequest
from app.services.room_service import RoomService


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
async def test_list_rooms_returns_pic_storage_key():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(
                rows=[
                    {
                        "store_room_id": 1,
                        "store_id": 10,
                        "name": "Room A",
                        "is_active": True,
                        "pic_storage_key": "stores/10/rooms/1.webp",
                    }
                ]
            ),
            FakeResult(scalar=1),
        ]
    )
    service = RoomService(session=session)

    response = await service.list_rooms(store_id=10, limit=20, offset=0)

    assert response.items[0].pic_storage_key == "stores/10/rooms/1.webp"


@pytest.mark.asyncio
async def test_create_room_returns_pic_storage_key():
    session = FakeSession(
        [
            FakeResult(scalar_or_none=1),
            FakeResult(
                rows=[
                    {
                        "store_room_id": 1,
                        "store_id": 10,
                        "name": "Room A",
                        "is_active": True,
                        "pic_storage_key": "stores/10/rooms/1.webp",
                    }
                ]
            ),
        ]
    )
    service = RoomService(session=session)

    item = await service.create_room(
        store_id=10,
        payload=CreateRoomRequest(
            name="Room A",
            pic_storage_key="stores/10/rooms/1.webp",
        ),
    )

    assert item.pic_storage_key == "stores/10/rooms/1.webp"


@pytest.mark.asyncio
async def test_update_room_can_clear_pic_storage_key():
    session = FakeSession(
        [
            FakeResult(
                rows=[
                    {
                        "store_room_id": 1,
                        "store_id": 10,
                        "name": "Room A",
                        "is_active": True,
                        "pic_storage_key": None,
                    }
                ]
            )
        ]
    )
    service = RoomService(session=session)

    item = await service.update_room(
        store_id=10,
        store_room_id=1,
        payload=UpdateRoomRequest(pic_storage_key=None),
    )

    assert item.pic_storage_key is None
    _, params = session.execute_calls[0]
    assert "pic_storage_key" in params
    assert params["pic_storage_key"] is None


@pytest.mark.asyncio
async def test_list_rooms_store_missing():
    session = FakeSession([FakeResult(scalar_or_none=None)])
    service = RoomService(session=session)

    with pytest.raises(NotFoundError):
        await service.list_rooms(store_id=10, limit=20, offset=0)
