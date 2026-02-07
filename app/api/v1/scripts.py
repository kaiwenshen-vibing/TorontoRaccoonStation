from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_script_service
from app.schemas.script import ScriptListResponse
from app.services.script_service import ScriptService

router = APIRouter(prefix="/stores/{store_id}/scripts")


@router.get("", response_model=ScriptListResponse)
async def list_scripts(
    store_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ScriptService = Depends(get_script_service),
) -> ScriptListResponse:
    return await service.list_store_scripts(store_id=store_id, limit=limit, offset=offset)

