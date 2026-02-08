from pydantic import BaseModel, Field, model_validator


class ScriptItem(BaseModel):
    script_id: int
    name: str
    estimated_minutes: int


class ScriptListResponse(BaseModel):
    items: list[ScriptItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class CreateScriptRequest(BaseModel):
    name: str = Field(min_length=1)
    estimated_minutes: int = Field(ge=1)


class UpdateScriptRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    estimated_minutes: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_changes(self) -> "UpdateScriptRequest":
        if self.name is None and self.estimated_minutes is None:
            raise ValueError("At least one field must be provided.")
        return self


class StoreScriptItem(BaseModel):
    script_id: int
    name: str
    estimated_minutes: int
    is_active: bool


class StoreScriptListResponse(BaseModel):
    items: list[StoreScriptItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class CreateStoreScriptRequest(BaseModel):
    script_id: int = Field(ge=1)
    is_active: bool = True


class UpdateStoreScriptRequest(BaseModel):
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "UpdateStoreScriptRequest":
        if self.is_active is None:
            raise ValueError("At least one field must be provided.")
        return self
