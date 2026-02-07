from fastapi import APIRouter

from app.api.v1.bookings import router as bookings_router
from app.api.v1.rooms import router as rooms_router
from app.api.v1.scripts import router as scripts_router
from app.api.v1.slots import router as slots_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(bookings_router, tags=["bookings"])
v1_router.include_router(slots_router, tags=["slots"])
v1_router.include_router(rooms_router, tags=["rooms"])
v1_router.include_router(scripts_router, tags=["scripts"])

