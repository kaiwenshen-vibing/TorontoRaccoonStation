from fastapi import APIRouter, Depends, Query, Response

from app.core.dependencies import get_script_service
from app.schemas.script import (
    CreateStoreScriptRequest,
    StoreScriptItem,
    StoreScriptListResponse,
    UpdateStoreScriptRequest,
)
from app.services.script_service import ScriptService

router = APIRouter(prefix="/stores/{store_id}/scripts")


@router.get("", response_model=StoreScriptListResponse)
async def list_store_scripts(
    store_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ScriptService = Depends(get_script_service),
) -> StoreScriptListResponse:
    return await service.list_store_scripts(store_id=store_id, limit=limit, offset=offset)


@router.post("", response_model=StoreScriptItem, status_code=201)
async def create_store_script(
    store_id: int,
    payload: CreateStoreScriptRequest,
    service: ScriptService = Depends(get_script_service),
) -> StoreScriptItem:
    return await service.create_store_script(store_id=store_id, payload=payload)


@router.patch("/{script_id}", response_model=StoreScriptItem)
async def update_store_script(
    store_id: int,
    script_id: int,
    payload: UpdateStoreScriptRequest,
    service: ScriptService = Depends(get_script_service),
) -> StoreScriptItem:
    return await service.update_store_script(
        store_id=store_id,
        script_id=script_id,
        payload=payload,
    )


@router.delete("/{script_id}", status_code=204)
async def delete_store_script(
    store_id: int,
    script_id: int,
    service: ScriptService = Depends(get_script_service),
) -> Response:
    await service.delete_store_script(store_id=store_id, script_id=script_id)
    return Response(status_code=204)
