from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.models.project import PipelineStep, Project
from app.services.pipeline import PipelineOrchestrator

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

VALID_STATUSES = {"pending", "running", "completed", "failed"}
ALREADY_RUNNING_STATUS = "running"
CANCELLED_STATUS = "cancelled"


class PipelineStartResponse(BaseModel):
    project_id: int
    status: str
    active_steps: list[str]


class PipelineStepStatus(BaseModel):
    step: str
    status: str
    error_message: str | None = None
    duration_ms: int | None = None


class PipelineStatusResponse(BaseModel):
    project_id: int
    status: str
    steps: list[PipelineStepStatus]


def _get_user_project(
    project_id: int, user_id: str, db: Session
) -> Project:
    """프로젝트를 조회하고 소유권을 검증한다."""
    project = db.query(Project).filter_by(id=project_id, user_id=user_id).first()
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"프로젝트를 찾을 수 없습니다: id={project_id}",
        )
    return project


@router.post("/{project_id}/start", response_model=PipelineStartResponse)
async def start_pipeline(
    project_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    project = _get_user_project(project_id, user_id, db)

    if project.status == ALREADY_RUNNING_STATUS:
        raise HTTPException(
            status_code=409,
            detail=f"파이프라인이 이미 실행 중입니다: id={project_id}",
        )

    orchestrator = PipelineOrchestrator(project.pipeline_config or {})
    active_steps = orchestrator.get_active_steps()

    for step_name in active_steps:
        step = PipelineStep(
            project_id=project.id,
            step=step_name,
            status="pending",
        )
        db.add(step)

    project.status = ALREADY_RUNNING_STATUS
    db.commit()
    db.refresh(project)

    return PipelineStartResponse(
        project_id=project.id,
        status=project.status,
        active_steps=active_steps,
    )


@router.get("/{project_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    project_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    project = _get_user_project(project_id, user_id, db)

    steps = (
        db.query(PipelineStep)
        .filter_by(project_id=project.id)
        .all()
    )

    return PipelineStatusResponse(
        project_id=project.id,
        status=project.status,
        steps=[
            PipelineStepStatus(
                step=s.step,
                status=s.status,
                error_message=s.error_message,
                duration_ms=s.duration_ms,
            )
            for s in steps
        ],
    )


@router.post("/{project_id}/cancel", response_model=PipelineStatusResponse)
async def cancel_pipeline(
    project_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    project = _get_user_project(project_id, user_id, db)

    project.status = CANCELLED_STATUS

    running_steps = (
        db.query(PipelineStep)
        .filter_by(project_id=project.id, status=ALREADY_RUNNING_STATUS)
        .all()
    )
    for step in running_steps:
        step.status = CANCELLED_STATUS

    db.commit()
    db.refresh(project)

    all_steps = (
        db.query(PipelineStep)
        .filter_by(project_id=project.id)
        .all()
    )

    return PipelineStatusResponse(
        project_id=project.id,
        status=project.status,
        steps=[
            PipelineStepStatus(
                step=s.step,
                status=s.status,
                error_message=s.error_message,
                duration_ms=s.duration_ms,
            )
            for s in all_steps
        ],
    )
