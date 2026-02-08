from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.schemas.script_character import (
    CreateScriptCharacterRequest,
    ScriptCharacterItem,
    ScriptCharacterListResponse,
    UpdateScriptCharacterRequest,
)
from app.services.base import BaseService


class ScriptCharacterService(BaseService):
    async def _assert_script_exists(self, script_id: int) -> None:
        result = await self.session.execute(
            text("SELECT 1 FROM script WHERE script_id = :script_id"),
            {"script_id": script_id},
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundError(f"script_id={script_id} was not found.")

    async def list_script_characters(
        self, script_id: int, limit: int, offset: int
    ) -> ScriptCharacterListResponse:
        await self._assert_script_exists(script_id=script_id)
        items_result = await self.session.execute(
            text(
                """
                SELECT character_id, script_id, character_name, is_dm, is_active
                FROM script_character
                WHERE script_id = :script_id
                ORDER BY updated_at DESC, character_id DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {"script_id": script_id, "limit": limit, "offset": offset},
        )
        items = [ScriptCharacterItem(**row) for row in items_result.mappings().all()]
        total_result = await self.session.execute(
            text("SELECT count(*) FROM script_character WHERE script_id = :script_id"),
            {"script_id": script_id},
        )
        total = total_result.scalar_one()
        return ScriptCharacterListResponse(items=items, limit=limit, offset=offset, total=total)

    async def create_script_character(
        self, script_id: int, payload: CreateScriptCharacterRequest
    ) -> ScriptCharacterItem:
        await self._assert_script_exists(script_id=script_id)
        try:
            async with self.session.begin():
                result = await self.session.execute(
                    text(
                        """
                        INSERT INTO script_character (script_id, character_name, is_dm, is_active)
                        VALUES (:script_id, :character_name, :is_dm, :is_active)
                        RETURNING character_id, script_id, character_name, is_dm, is_active
                        """
                    ),
                    {"script_id": script_id, **payload.model_dump()},
                )
                row = result.mappings().one()
        except IntegrityError as exc:
            raise ConflictError("character name already exists for this script.") from exc
        return ScriptCharacterItem(**row)

    async def get_script_character(self, script_id: int, character_id: int) -> ScriptCharacterItem:
        result = await self.session.execute(
            text(
                """
                SELECT character_id, script_id, character_name, is_dm, is_active
                FROM script_character
                WHERE script_id = :script_id
                  AND character_id = :character_id
                """
            ),
            {"script_id": script_id, "character_id": character_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise NotFoundError(
                f"script_id={script_id} does not have character_id={character_id}."
            )
        return ScriptCharacterItem(**row)

    async def update_script_character(
        self,
        script_id: int,
        character_id: int,
        payload: UpdateScriptCharacterRequest,
    ) -> ScriptCharacterItem:
        values = {"script_id": script_id, "character_id": character_id}
        updates = []
        if payload.character_name is not None:
            updates.append("character_name = :character_name")
            values["character_name"] = payload.character_name
        if payload.is_dm is not None:
            updates.append("is_dm = :is_dm")
            values["is_dm"] = payload.is_dm
        if payload.is_active is not None:
            updates.append("is_active = :is_active")
            values["is_active"] = payload.is_active
        updates.append("updated_at = now()")
        query = f"""
            UPDATE script_character
            SET {", ".join(updates)}
            WHERE script_id = :script_id
              AND character_id = :character_id
            RETURNING character_id, script_id, character_name, is_dm, is_active
        """
        try:
            async with self.session.begin():
                result = await self.session.execute(text(query), values)
                row = result.mappings().one_or_none()
                if row is None:
                    raise NotFoundError(
                        f"script_id={script_id} does not have character_id={character_id}."
                    )
        except IntegrityError as exc:
            raise ConflictError("character name already exists for this script.") from exc
        return ScriptCharacterItem(**row)

    async def delete_script_character(self, script_id: int, character_id: int) -> None:
        async with self.session.begin():
            result = await self.session.execute(
                text(
                    """
                    DELETE FROM script_character
                    WHERE script_id = :script_id
                      AND character_id = :character_id
                    RETURNING character_id
                    """
                ),
                {"script_id": script_id, "character_id": character_id},
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError(
                    f"script_id={script_id} does not have character_id={character_id}."
                )
