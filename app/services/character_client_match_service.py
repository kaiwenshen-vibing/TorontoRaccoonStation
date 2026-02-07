from app.core.errors import FeatureNotImplementedError
from app.schemas.booking import (
    CharacterClientMatchItem,
    CreateCharacterClientMatchRequest,
    UpdateCharacterClientMatchRequest,
)
from app.services.base import BaseService


class CharacterClientMatchService(BaseService):
    async def create_match(
        self,
        store_id: int,
        booking_id: int,
        payload: CreateCharacterClientMatchRequest,
    ) -> CharacterClientMatchItem:
        raise FeatureNotImplementedError("create character_client_match is not implemented yet.")

    async def update_match(
        self,
        store_id: int,
        booking_id: int,
        match_id: int,
        payload: UpdateCharacterClientMatchRequest,
    ) -> CharacterClientMatchItem:
        raise FeatureNotImplementedError("update character_client_match is not implemented yet.")

    async def delete_match(self, store_id: int, booking_id: int, match_id: int) -> None:
        raise FeatureNotImplementedError("delete character_client_match is not implemented yet.")

