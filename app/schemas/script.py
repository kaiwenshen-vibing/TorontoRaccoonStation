from pydantic import BaseModel, Field


class ScriptItem(BaseModel):
    script_id: int
    name: str
    estimated_minutes: int
    is_active: bool


class ScriptListResponse(BaseModel):
    items: list[ScriptItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int

