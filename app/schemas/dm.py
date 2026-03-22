from pydantic import BaseModel, Field, model_validator


class DmItem(BaseModel):
    dm_id: int
    display_name: str
    is_active: bool
    pic_storage_key: str | None = None


class DmListResponse(BaseModel):
    items: list[DmItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class CreateDmRequest(BaseModel):
    display_name: str = Field(min_length=1)
    is_active: bool = True
    pic_storage_key: str | None = None


class UpdateDmRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None
    pic_storage_key: str | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "UpdateDmRequest":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self


class DmStoreMembershipItem(BaseModel):
    store_id: int
    store_name: str


class DmStoreMembershipListResponse(BaseModel):
    items: list[DmStoreMembershipItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class CreateDmStoreMembershipRequest(BaseModel):
    store_id: int = Field(ge=1)
