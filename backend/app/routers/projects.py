from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.dependencies import get_current_user_id
from app.schemas.project import ProjectCreate, ProjectListResponse, ProjectResponse
from app.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/projects", tags=["projects"])

VALID_TYPES = {"shorts", "longform"}


@router.post("", status_code=201, response_model=ProjectResponse)
async def create_project(
    body: ProjectCreate,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    # 1. Plan Check
    res = supabase.table("users").select("plan").filter("id", "eq", user_id).execute()
    user_plan = res.data[0].get("plan", "free") if res.data else "free"

    if user_plan == "free":
        # 2. Monthly Usage Check
        # Supabase filtering for dates: use ISO format
        first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        count_res = supabase.table("projects") \
            .select("id", count="exact") \
            .filter("user_id", "eq", user_id) \
            .filter("created_at", "gte", first_day_of_month) \
            .execute()
        
        project_count = count_res.count if count_res.count is not None else 0
        
        if project_count >= 5:
            raise HTTPException(
                status_code=402,
                detail="이번 달 무료 생성 한도(5개)를 초과했습니다. Pro 요금제로 업그레이드하고 무제한으로 이용해 보세요!",
            )

    if body.type not in VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"지원하지 않는 영상 유형입니다: {body.type}. "
                f"지원 목록: {', '.join(sorted(VALID_TYPES))}"
            ),
        )

    # 3. Create Project
    data = {
        "user_id": user_id,
        "title": body.title,
        "type": body.type,
        "topic": body.topic,
        "pipeline_config": body.pipeline_config,
        "status": "pending"
    }
    
    insert_res = supabase.table("projects").insert(data).execute()
    
    if not insert_res.data:
        raise HTTPException(status_code=500, detail="프로젝트 생성에 실패했습니다.")
        
    return insert_res.data[0]


@router.get("", response_model=list[ProjectListResponse])
async def list_projects(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    res = supabase.table("projects") \
        .select("*") \
        .filter("user_id", "eq", user_id) \
        .order("created_at", desc=True) \
        .execute()
        
    return res.data


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    res = supabase.table("projects") \
        .select("*") \
        .filter("id", "eq", project_id) \
        .filter("user_id", "eq", user_id) \
        .execute()
        
    if not res.data:
        raise HTTPException(
            status_code=404,
            detail=f"프로젝트를 찾을 수 없습니다: id={project_id}",
        )
    return res.data[0]


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    res = supabase.table("projects") \
        .delete() \
        .filter("id", "eq", project_id) \
        .filter("user_id", "eq", user_id) \
        .execute()
    
    if not res.data:
        raise HTTPException(
            status_code=404,
            detail=f"프로젝트를 찾을 수 없습니다: id={project_id}",
        )
