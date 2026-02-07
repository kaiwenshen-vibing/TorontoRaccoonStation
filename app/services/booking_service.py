from app.core.errors import FeatureNotImplementedError
from app.schemas.booking import (
    AddBookingClientRequest,
    BookingItem,
    BookingListResponse,
    ConfirmBookingRequest,
    CreateIncompleteBookingRequest,
    UpdateIncompleteBookingRequest,
)
from app.services.base import BaseService


class BookingService(BaseService):
    async def create_incomplete_booking(
        self,
        store_id: int,
        payload: CreateIncompleteBookingRequest,
    ) -> BookingItem:
        raise FeatureNotImplementedError("create_incomplete_booking is not implemented yet.")

    async def list_bookings(
        self,
        store_id: int,
        *,
        booking_status_id: int | None,
        target_month: str | None,
        has_conflict: bool | None,
        limit: int,
        offset: int,
    ) -> BookingListResponse:
        raise FeatureNotImplementedError("list_bookings is not implemented yet.")

    async def get_booking(self, store_id: int, booking_id: int) -> BookingItem:
        raise FeatureNotImplementedError("get_booking is not implemented yet.")

    async def update_incomplete_booking(
        self,
        store_id: int,
        booking_id: int,
        payload: UpdateIncompleteBookingRequest,
    ) -> BookingItem:
        raise FeatureNotImplementedError("update_incomplete_booking is not implemented yet.")

    async def confirm_booking(
        self,
        store_id: int,
        booking_id: int,
        payload: ConfirmBookingRequest,
    ) -> BookingItem:
        raise FeatureNotImplementedError("confirm_booking is not implemented yet.")

    async def cancel_booking(self, store_id: int, booking_id: int) -> BookingItem:
        raise FeatureNotImplementedError("cancel_booking is not implemented yet.")

    async def complete_booking(self, store_id: int, booking_id: int) -> BookingItem:
        raise FeatureNotImplementedError("complete_booking is not implemented yet.")

    async def add_booking_client(
        self,
        store_id: int,
        booking_id: int,
        payload: AddBookingClientRequest,
    ) -> BookingItem:
        raise FeatureNotImplementedError("add_booking_client is not implemented yet.")

    async def remove_booking_client(
        self,
        store_id: int,
        booking_id: int,
        client_id: int,
    ) -> BookingItem:
        raise FeatureNotImplementedError("remove_booking_client is not implemented yet.")

