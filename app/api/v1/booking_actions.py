from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_booking_service
from app.schemas.booking import BookingItem, BookingListResponse, ConfirmBookingRequest
from app.services.booking_service import BookingService

router = APIRouter(prefix="/stores/{store_id}/bookings")


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
