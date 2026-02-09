from fastapi import APIRouter, Depends, Response, status

from app.core.dependencies import (
    get_booking_service,
    get_character_client_match_service,
    get_character_dm_match_service,
)
from app.schemas.booking import (
    AddBookingClientRequest,
    BookingItem,
    CharacterClientMatchItem,
    CharacterDmMatchItem,
    CreateCharacterClientMatchRequest,
    CreateCharacterDmMatchRequest,
    UpdateCharacterClientMatchRequest,
    UpdateCharacterDmMatchRequest,
)
from app.services.booking_service import BookingService
from app.services.character_client_match_service import CharacterClientMatchService
from app.services.character_dm_match_service import CharacterDmMatchService

router = APIRouter(prefix="/stores/{store_id}/bookings/{booking_id}")


@router.post("/clients", response_model=BookingItem)
async def add_booking_client(
    store_id: int,
    booking_id: int,
    payload: AddBookingClientRequest,
    service: BookingService = Depends(get_booking_service),
) -> BookingItem:
    return await service.add_booking_client(store_id=store_id, booking_id=booking_id, payload=payload)


@router.delete("/clients/{client_id}", response_model=BookingItem)
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
    "/character-client-matches",
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


@router.patch("/character-client-matches/{match_id}", response_model=CharacterClientMatchItem)
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


@router.delete("/character-client-matches/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character_client_match(
    store_id: int,
    booking_id: int,
    match_id: int,
    service: CharacterClientMatchService = Depends(get_character_client_match_service),
) -> Response:
    await service.delete_match(store_id=store_id, booking_id=booking_id, match_id=match_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/character-dm-matches",
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


@router.patch("/character-dm-matches/{match_id}", response_model=CharacterDmMatchItem)
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


@router.delete("/character-dm-matches/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character_dm_match(
    store_id: int,
    booking_id: int,
    match_id: int,
    service: CharacterDmMatchService = Depends(get_character_dm_match_service),
) -> Response:
    await service.delete_match(store_id=store_id, booking_id=booking_id, match_id=match_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
