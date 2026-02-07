from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import (
    get_booking_service,
    get_character_client_match_service,
    get_character_dm_match_service,
)
from app.schemas.booking import (
    AddBookingClientRequest,
    BookingItem,
    BookingListResponse,
    CharacterClientMatchItem,
    CharacterDmMatchItem,
    ConfirmBookingRequest,
    CreateCharacterClientMatchRequest,
    CreateCharacterDmMatchRequest,
    CreateIncompleteBookingRequest,
    UpdateCharacterClientMatchRequest,
    UpdateCharacterDmMatchRequest,
    UpdateIncompleteBookingRequest,
)
from app.services.booking_service import BookingService
from app.services.character_client_match_service import CharacterClientMatchService
from app.services.character_dm_match_service import CharacterDmMatchService

router = APIRouter(prefix="/stores/{store_id}/bookings")


@router.post("/incomplete", response_model=BookingItem, status_code=status.HTTP_201_CREATED)
async def create_incomplete_booking(
    store_id: int,
    payload: CreateIncompleteBookingRequest,
    service: BookingService = Depends(get_booking_service),
) -> BookingItem:
    return await service.create_incomplete_booking(store_id=store_id, payload=payload)


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    store_id: int,
    booking_status_id: int | None = Query(default=None, ge=1),
    target_month: date | None = Query(default=None),
    has_conflict: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: BookingService = Depends(get_booking_service),
) -> BookingListResponse:
    target_month_value = target_month.isoformat() if target_month else None
    return await service.list_bookings(
        store_id=store_id,
        booking_status_id=booking_status_id,
        target_month=target_month_value,
        has_conflict=has_conflict,
        limit=limit,
        offset=offset,
    )


@router.get("/{booking_id}", response_model=BookingItem)
async def get_booking(
    store_id: int,
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
) -> BookingItem:
    return await service.get_booking(store_id=store_id, booking_id=booking_id)


@router.patch("/{booking_id}", response_model=BookingItem)
async def update_incomplete_booking(
    store_id: int,
    booking_id: int,
    payload: UpdateIncompleteBookingRequest,
    service: BookingService = Depends(get_booking_service),
) -> BookingItem:
    return await service.update_incomplete_booking(
        store_id=store_id,
        booking_id=booking_id,
        payload=payload,
    )


@router.post("/{booking_id}/confirm", response_model=BookingItem)
async def confirm_booking(
    store_id: int,
    booking_id: int,
    payload: ConfirmBookingRequest,
    service: BookingService = Depends(get_booking_service),
) -> BookingItem:
    return await service.confirm_booking(store_id=store_id, booking_id=booking_id, payload=payload)


@router.post("/{booking_id}/cancel", response_model=BookingItem)
async def cancel_booking(
    store_id: int,
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
) -> BookingItem:
    return await service.cancel_booking(store_id=store_id, booking_id=booking_id)


@router.post("/{booking_id}/complete", response_model=BookingItem)
async def complete_booking(
    store_id: int,
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
) -> BookingItem:
    return await service.complete_booking(store_id=store_id, booking_id=booking_id)


@router.post("/{booking_id}/clients", response_model=BookingItem)
async def add_booking_client(
    store_id: int,
    booking_id: int,
    payload: AddBookingClientRequest,
    service: BookingService = Depends(get_booking_service),
) -> BookingItem:
    return await service.add_booking_client(store_id=store_id, booking_id=booking_id, payload=payload)


@router.delete("/{booking_id}/clients/{client_id}", response_model=BookingItem)
async def remove_booking_client(
    store_id: int,
    booking_id: int,
    client_id: int,
    service: BookingService = Depends(get_booking_service),
) -> BookingItem:
    return await service.remove_booking_client(
        store_id=store_id,
        booking_id=booking_id,
        client_id=client_id,
    )


@router.post(
    "/{booking_id}/character-client-matches",
    response_model=CharacterClientMatchItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_character_client_match(
    store_id: int,
    booking_id: int,
    payload: CreateCharacterClientMatchRequest,
    service: CharacterClientMatchService = Depends(get_character_client_match_service),
) -> CharacterClientMatchItem:
    return await service.create_match(store_id=store_id, booking_id=booking_id, payload=payload)


@router.patch("/{booking_id}/character-client-matches/{match_id}", response_model=CharacterClientMatchItem)
async def update_character_client_match(
    store_id: int,
    booking_id: int,
    match_id: int,
    payload: UpdateCharacterClientMatchRequest,
    service: CharacterClientMatchService = Depends(get_character_client_match_service),
) -> CharacterClientMatchItem:
    return await service.update_match(
        store_id=store_id,
        booking_id=booking_id,
        match_id=match_id,
        payload=payload,
    )


@router.delete("/{booking_id}/character-client-matches/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character_client_match(
    store_id: int,
    booking_id: int,
    match_id: int,
    service: CharacterClientMatchService = Depends(get_character_client_match_service),
) -> Response:
    await service.delete_match(store_id=store_id, booking_id=booking_id, match_id=match_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{booking_id}/character-dm-matches",
    response_model=CharacterDmMatchItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_character_dm_match(
    store_id: int,
    booking_id: int,
    payload: CreateCharacterDmMatchRequest,
    service: CharacterDmMatchService = Depends(get_character_dm_match_service),
) -> CharacterDmMatchItem:
    return await service.create_match(store_id=store_id, booking_id=booking_id, payload=payload)


@router.patch("/{booking_id}/character-dm-matches/{match_id}", response_model=CharacterDmMatchItem)
async def update_character_dm_match(
    store_id: int,
    booking_id: int,
    match_id: int,
    payload: UpdateCharacterDmMatchRequest,
    service: CharacterDmMatchService = Depends(get_character_dm_match_service),
) -> CharacterDmMatchItem:
    return await service.update_match(
        store_id=store_id,
        booking_id=booking_id,
        match_id=match_id,
        payload=payload,
    )


@router.delete("/{booking_id}/character-dm-matches/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character_dm_match(
    store_id: int,
    booking_id: int,
    match_id: int,
    service: CharacterDmMatchService = Depends(get_character_dm_match_service),
) -> Response:
    await service.delete_match(store_id=store_id, booking_id=booking_id, match_id=match_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

