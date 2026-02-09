from fastapi import APIRouter

from app.api.v1.booking_actions import router as booking_actions_router
from app.api.v1.booking_details import router as booking_details_router
from app.api.v1.incomplete_bookings import router as incomplete_bookings_router
from app.api.v1.rooms import router as rooms_router
from app.api.v1.script_characters import router as script_characters_router
from app.api.v1.scripts import router as scripts_router
from app.api.v1.store_scripts import router as store_scripts_router
from app.api.v1.slots import router as slots_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(incomplete_bookings_router, tags=["incomplete-bookings"])
v1_router.include_router(booking_actions_router, tags=["bookings"])
v1_router.include_router(booking_details_router, tags=["booking-details"])
v1_router.include_router(slots_router, tags=["slots"])
v1_router.include_router(rooms_router, tags=["rooms"])
v1_router.include_router(scripts_router, tags=["scripts"])
v1_router.include_router(store_scripts_router, tags=["store-scripts"])
v1_router.include_router(script_characters_router, tags=["script-characters"])
