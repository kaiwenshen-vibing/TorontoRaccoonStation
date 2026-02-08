from fastapi import APIRouter, Depends, Query, Response

from app.core.dependencies import get_global_script_service
from app.schemas.script import (
    CreateScriptRequest,
    ScriptItem,
    ScriptListResponse,
    UpdateScriptRequest,
)
from app.services.script_service import ScriptService

router = APIRouter(prefix="/scripts")


@router.get("", response_model=ScriptListResponse)
async def list_scripts(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ScriptService = Depends(get_global_script_service),
) -> ScriptListResponse:
    return await service.list_scripts(limit=limit, offset=offset)


@router.post("", response_model=ScriptItem, status_code=201)
async def create_script(
    payload: CreateScriptRequest,
    service: ScriptService = Depends(get_global_script_service),
) -> ScriptItem:
    return await service.create_script(payload=payload)


@router.get("/{script_id}", response_model=ScriptItem)
async def get_script(
    script_id: int,
    service: ScriptService = Depends(get_global_script_service),
) -> ScriptItem:
    return await service.get_script(script_id=script_id)


@router.patch("/{script_id}", response_model=ScriptItem)
async def update_script(
    script_id: int,
    payload: UpdateScriptRequest,
    service: ScriptService = Depends(get_global_script_service),
) -> ScriptItem:
    return await service.update_script(script_id=script_id, payload=payload)


@router.delete("/{script_id}", status_code=204)
async def delete_script(
    script_id: int,
    service: ScriptService = Depends(get_global_script_service),
) -> Response:
    await service.delete_script(script_id=script_id)
    return Response(status_code=204)
