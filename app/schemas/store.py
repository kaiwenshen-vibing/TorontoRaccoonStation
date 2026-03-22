from pydantic import BaseModel, Field, model_validator


class StoreItem(BaseModel):
    store_id: int
    name: str
    pic_storage_key: str | None = None


class StoreListResponse(BaseModel):
    items: list[StoreItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class CreateStoreRequest(BaseModel):
    name: str = Field(min_length=1)
    pic_storage_key: str | None = None


class UpdateStoreRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    pic_storage_key: str | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "UpdateStoreRequest":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self
