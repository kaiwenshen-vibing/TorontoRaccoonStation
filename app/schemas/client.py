from pydantic import BaseModel, Field, model_validator


class ClientItem(BaseModel):
    client_id: int
    display_name: str
    phone: str | None = None
    pic_storage_key: str | None = None


class ClientListResponse(BaseModel):
    items: list[ClientItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class CreateClientRequest(BaseModel):
    display_name: str = Field(min_length=1)
    phone: str | None = None
    pic_storage_key: str | None = None


class UpdateClientRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1)
    phone: str | None = None
    pic_storage_key: str | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "UpdateClientRequest":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self
