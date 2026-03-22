from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import ActorContext, get_actor_context, get_scoped_store_service, get_store_service
from app.schemas.store import CreateStoreRequest, StoreItem, StoreListResponse, UpdateStoreRequest
from app.services.store_service import StoreService

router = APIRouter(prefix="/stores")


@router.get("", response_model=StoreListResponse)
async def list_stores(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: ActorContext = Depends(get_actor_context),
    service: StoreService = Depends(get_store_service),
) -> StoreListResponse:
    return await service.list_stores(
        allowed_store_ids=actor.allowed_store_ids,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=StoreItem, status_code=status.HTTP_201_CREATED)
async def create_store(
    payload: CreateStoreRequest,
    service: StoreService = Depends(get_store_service),
) -> StoreItem:
    return await service.create_store(payload=payload)


@router.get("/{store_id}", response_model=StoreItem)
async def get_store(
    store_id: int,
    service: StoreService = Depends(get_scoped_store_service),
) -> StoreItem:
    return await service.get_store(store_id=store_id)


@router.patch("/{store_id}", response_model=StoreItem)
async def update_store(
    store_id: int,
    payload: UpdateStoreRequest,
    service: StoreService = Depends(get_scoped_store_service),
) -> StoreItem:
    return await service.update_store(store_id=store_id, payload=payload)


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(
    store_id: int,
    service: StoreService = Depends(get_scoped_store_service),
) -> Response:
    await service.delete_store(store_id=store_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
