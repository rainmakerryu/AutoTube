from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    type: str
    topic: str
    pipeline_config: dict


class ProjectResponse(BaseModel):
    id: int
    title: str
    type: str
    topic: str
    status: str
    pipeline_config: dict
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    id: int
    title: str
    type: str
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
