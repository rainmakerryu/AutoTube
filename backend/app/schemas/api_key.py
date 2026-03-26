from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    provider: str
    key: str


class ApiKeyResponse(BaseModel):
    id: int
    provider: str
    masked_key: str
    is_valid: bool

    model_config = {"from_attributes": True}
