from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    provider: str
    key: str = Field(alias="api_key")

    model_config = {"populate_by_name": True}


class ApiKeyResponse(BaseModel):
    id: int
    provider: str
    masked_key: str
    is_valid: bool

    model_config = {"from_attributes": True}
