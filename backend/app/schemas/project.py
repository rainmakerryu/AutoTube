from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    type: str
    topic: str
    pipeline_config: dict[str, bool]


class ProjectResponse(BaseModel):
    id: int
    title: str
    type: str
    topic: str
    status: str
    pipeline_config: dict
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    id: int
    title: str
    type: str
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
