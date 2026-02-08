from pydantic import BaseModel, Field, model_validator


class ScriptCharacterItem(BaseModel):
    character_id: int
    script_id: int
    character_name: str
    is_dm: bool
    is_active: bool


class ScriptCharacterListResponse(BaseModel):
    items: list[ScriptCharacterItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class CreateScriptCharacterRequest(BaseModel):
    character_name: str = Field(min_length=1)
    is_dm: bool = False
    is_active: bool = True


class UpdateScriptCharacterRequest(BaseModel):
    character_name: str | None = Field(default=None, min_length=1)
    is_dm: bool | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "UpdateScriptCharacterRequest":
        if self.character_name is None and self.is_dm is None and self.is_active is None:
            raise ValueError("At least one field must be provided.")
        return self
