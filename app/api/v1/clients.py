from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import get_client_service
from app.schemas.client import ClientItem, ClientListResponse, CreateClientRequest, UpdateClientRequest
from app.services.client_service import ClientService

router = APIRouter(prefix="/clients")


@router.get("", response_model=ClientListResponse)
async def list_clients(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ClientService = Depends(get_client_service),
) -> ClientListResponse:
    return await service.list_clients(limit=limit, offset=offset)


@router.post("", response_model=ClientItem, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: CreateClientRequest,
    service: ClientService = Depends(get_client_service),
) -> ClientItem:
    return await service.create_client(payload=payload)


@router.get("/{client_id}", response_model=ClientItem)
async def get_client(
    client_id: int,
    service: ClientService = Depends(get_client_service),
) -> ClientItem:
    return await service.get_client(client_id=client_id)


@router.patch("/{client_id}", response_model=ClientItem)
async def update_client(
    client_id: int,
    payload: UpdateClientRequest,
    service: ClientService = Depends(get_client_service),
) -> ClientItem:
    return await service.update_client(client_id=client_id, payload=payload)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    service: ClientService = Depends(get_client_service),
) -> Response:
    await service.delete_client(client_id=client_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
