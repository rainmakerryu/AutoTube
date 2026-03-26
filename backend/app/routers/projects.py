from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectListResponse, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])

VALID_TYPES = {"shorts", "longform"}


@router.post("", status_code=201, response_model=ProjectResponse)
async def create_project(
    body: ProjectCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if body.type not in VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"지원하지 않는 영상 유형입니다: {body.type}. "
                f"지원 목록: {', '.join(sorted(VALID_TYPES))}"
            ),
        )

    project = Project(
        user_id=user_id,
        title=body.title,
        type=body.type,
        topic=body.topic,
        pipeline_config=body.pipeline_config,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectListResponse])
async def list_projects(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    projects = (
        db.query(Project)
        .filter_by(user_id=user_id)
        .order_by(Project.created_at.desc())
        .all()
    )
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter_by(id=project_id, user_id=user_id).first()
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"프로젝트를 찾을 수 없습니다: id={project_id}",
        )
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter_by(id=project_id, user_id=user_id).first()
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"프로젝트를 찾을 수 없습니다: id={project_id}",
        )
    db.delete(project)
    db.commit()
