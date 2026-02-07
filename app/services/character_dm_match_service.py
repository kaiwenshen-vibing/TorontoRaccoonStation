from app.core.errors import FeatureNotImplementedError
from app.schemas.booking import (
    CharacterDmMatchItem,
    CreateCharacterDmMatchRequest,
    UpdateCharacterDmMatchRequest,
)
from app.services.base import BaseService


class CharacterDmMatchService(BaseService):
    async def create_match(
        self,
        store_id: int,
        booking_id: int,
        payload: CreateCharacterDmMatchRequest,
    ) -> CharacterDmMatchItem:
        raise FeatureNotImplementedError("create character_dm_match is not implemented yet.")

    async def update_match(
        self,
        store_id: int,
        booking_id: int,
        match_id: int,
        payload: UpdateCharacterDmMatchRequest,
    ) -> CharacterDmMatchItem:
        raise FeatureNotImplementedError("update character_dm_match is not implemented yet.")

    async def delete_match(self, store_id: int, booking_id: int, match_id: int) -> None:
        raise FeatureNotImplementedError("delete character_dm_match is not implemented yet.")

