from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import get_script_character_service
from app.schemas.script_character import (
    CreateScriptCharacterRequest,
    ScriptCharacterItem,
    ScriptCharacterListResponse,
    UpdateScriptCharacterRequest,
)
from app.services.script_character_service import ScriptCharacterService

router = APIRouter(prefix="/scripts/{script_id}/characters")


@router.get("", response_model=ScriptCharacterListResponse)
async def list_script_characters(
    script_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ScriptCharacterService = Depends(get_script_character_service),
) -> ScriptCharacterListResponse:
    return await service.list_script_characters(script_id=script_id, limit=limit, offset=offset)


@router.post("", response_model=ScriptCharacterItem, status_code=status.HTTP_201_CREATED)
async def create_script_character(
    script_id: int,
    payload: CreateScriptCharacterRequest,
    service: ScriptCharacterService = Depends(get_script_character_service),
) -> ScriptCharacterItem:
    return await service.create_script_character(script_id=script_id, payload=payload)


@router.get("/{character_id}", response_model=ScriptCharacterItem)
async def get_script_character(
    script_id: int,
    character_id: int,
    service: ScriptCharacterService = Depends(get_script_character_service),
) -> ScriptCharacterItem:
    return await service.get_script_character(script_id=script_id, character_id=character_id)


@router.patch("/{character_id}", response_model=ScriptCharacterItem)
async def update_script_character(
    script_id: int,
    character_id: int,
    payload: UpdateScriptCharacterRequest,
    service: ScriptCharacterService = Depends(get_script_character_service),
) -> ScriptCharacterItem:
    return await service.update_script_character(
        script_id=script_id,
        character_id=character_id,
        payload=payload,
    )


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script_character(
    script_id: int,
    character_id: int,
    service: ScriptCharacterService = Depends(get_script_character_service),
) -> Response:
    await service.delete_script_character(script_id=script_id, character_id=character_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
