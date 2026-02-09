from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_booking_service
from app.schemas.booking import CreateIncompleteBookingRequest, BookingItem, UpdateIncompleteBookingRequest
from app.services.booking_service import BookingService

router = APIRouter(prefix="/stores/{store_id}/bookings")


@router.post("/incomplete", response_model=BookingItem, status_code=status.HTTP_201_CREATED)
async def create_incomplete_booking(
    store_id: int,
    payload: CreateIncompleteBookingRequest,
    service: BookingService = Depends(get_booking_service),
) -> BookingItem:
    return await service.create_incomplete_booking(store_id=store_id, payload=payload)


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
