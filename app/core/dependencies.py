from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.booking_service import BookingService
from app.services.character_client_match_service import CharacterClientMatchService
from app.services.character_dm_match_service import CharacterDmMatchService
from app.services.room_service import RoomService
from app.services.script_service import ScriptService
from app.services.slot_service import SlotService


@dataclass(slots=True)
class ActorContext:
    actor_id: str
    allowed_store_ids: set[int]


def get_actor_context(
    x_actor_id: str = Header(..., alias="X-Actor-Id"),
    x_allowed_store_ids: str = Header(..., alias="X-Allowed-Store-Ids"),
) -> ActorContext:
    raw_items = [item.strip() for item in x_allowed_store_ids.split(",") if item.strip()]
    if not raw_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Allowed-Store-Ids must include at least one store id.",
        )
    try:
        store_ids = {int(item) for item in raw_items}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Allowed-Store-Ids must be a comma-separated integer list.",
        ) from exc
    return ActorContext(actor_id=x_actor_id, allowed_store_ids=store_ids)


def require_store_access(
    store_id: int = Path(..., ge=1),
    actor: ActorContext = Depends(get_actor_context),
) -> ActorContext:
    if store_id not in actor.allowed_store_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"actor is not allowed to access store_id={store_id}",
        )
    return actor


def get_booking_service(
    _actor: ActorContext = Depends(require_store_access),
    session: AsyncSession = Depends(get_async_session),
) -> BookingService:
    return BookingService(session=session)


def get_slot_service(
    _actor: ActorContext = Depends(require_store_access),
    session: AsyncSession = Depends(get_async_session),
) -> SlotService:
    return SlotService(session=session)


def get_room_service(
    _actor: ActorContext = Depends(require_store_access),
    session: AsyncSession = Depends(get_async_session),
) -> RoomService:
    return RoomService(session=session)


def get_script_service(
    _actor: ActorContext = Depends(require_store_access),
    session: AsyncSession = Depends(get_async_session),
) -> ScriptService:
    return ScriptService(session=session)


def get_global_script_service(
    _actor: ActorContext = Depends(get_actor_context),
    session: AsyncSession = Depends(get_async_session),
) -> ScriptService:
    return ScriptService(session=session)


def get_character_client_match_service(
    _actor: ActorContext = Depends(require_store_access),
    session: AsyncSession = Depends(get_async_session),
) -> CharacterClientMatchService:
    return CharacterClientMatchService(session=session)


def get_character_dm_match_service(
    _actor: ActorContext = Depends(require_store_access),
    session: AsyncSession = Depends(get_async_session),
) -> CharacterDmMatchService:
    return CharacterDmMatchService(session=session)
