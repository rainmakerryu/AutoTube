from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from app.dependencies import get_current_user_id, get_encryption_service
from app.services.encryption import EncryptionService
from app.services.pipeline import PipelineOrchestrator, STEP_ORDER, STEP_PROVIDERS
from app.services.step_dispatcher import dispatch_step
from app.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

VALID_STATUSES = {
    "pending", "running", "completed", "failed",
    "cancelled", "awaiting_review", "approved",
}
ALREADY_RUNNING_STATUS = "running"
CANCELLED_STATUS = "cancelled"


class PipelineStartResponse(BaseModel):
    project_id: int
    status: str
    active_steps: list[str]


class PipelineStepStatus(BaseModel):
    step: str
    status: str
    provider: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None


class PipelineStatusResponse(BaseModel):
    project_id: int
    status: str
    steps: list[PipelineStepStatus]


class StepRunRequest(BaseModel):
    provider: str
    config: dict | None = None


class StepRunResponse(BaseModel):
    step: str
    status: str


class StepOutputResponse(BaseModel):
    step: str
    status: str
    output_data: dict | None = None


class StepApproveRequest(BaseModel):
    edited_data: dict | None = None


class StepRejectRequest(BaseModel):
    feedback: str | None = None


def _get_user_project(
    project_id: int, user_id: str, supabase: Client
) -> dict:
    """프로젝트를 조회하고 소유권을 검증한다."""
    res = supabase.table("projects").select("*").filter("id", "eq", project_id).filter("user_id", "eq", user_id).execute()
    if not res.data:
        raise HTTPException(
            status_code=404,
            detail=f"프로젝트를 찾을 수 없습니다: id={project_id}",
        )
    return res.data[0]


@router.post("/{project_id}/start", response_model=PipelineStartResponse)
async def start_pipeline(
    project_id: int,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    project = _get_user_project(project_id, user_id, supabase)

    if project.get("status") == ALREADY_RUNNING_STATUS:
        raise HTTPException(
            status_code=409,
            detail=f"파이프라인이 이미 실행 중입니다: id={project_id}",
        )

    orchestrator = PipelineOrchestrator(project.get("pipeline_config") or {})
    active_steps = orchestrator.get_active_steps()

    # Insert pipeline steps
    for step_name in active_steps:
        supabase.table("pipeline_steps").insert({
            "project_id": project["id"],
            "step": step_name,
            "status": "pending",
        }).execute()

    # Update project status
    update_res = supabase.table("projects").update({"status": ALREADY_RUNNING_STATUS}).filter("id", "eq", project["id"]).execute()
    
    updated_project = update_res.data[0]

    return PipelineStartResponse(
        project_id=updated_project["id"],
        status=updated_project["status"],
        active_steps=active_steps,
    )


@router.get("/{project_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    project_id: int,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    project = _get_user_project(project_id, user_id, supabase)

    steps_res = supabase.table("pipeline_steps") \
        .select("*") \
        .filter("project_id", "eq", project["id"]) \
        .execute()

    return PipelineStatusResponse(
        project_id=project["id"],
        status=project["status"],
        steps=[
            PipelineStepStatus(
                step=s["step"],
                status=s["status"],
                provider=s.get("provider"),
                error_message=s.get("error_message"),
                duration_ms=s.get("duration_ms"),
            )
            for s in steps_res.data
        ],
    )


@router.post("/{project_id}/cancel", response_model=PipelineStatusResponse)
async def cancel_pipeline(
    project_id: int,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    project = _get_user_project(project_id, user_id, supabase)

    # 1. Update project status to cancelled
    supabase.table("projects").update({"status": CANCELLED_STATUS}).filter("id", "eq", project["id"]).execute()

    # 2. Update running steps to cancelled
    supabase.table("pipeline_steps") \
        .update({"status": CANCELLED_STATUS}) \
        .filter("project_id", "eq", project["id"]) \
        .filter("status", "eq", ALREADY_RUNNING_STATUS) \
        .execute()

    # 3. Get all steps for response
    steps_res = supabase.table("pipeline_steps") \
        .select("*") \
        .filter("project_id", "eq", project["id"]) \
        .execute()

    return PipelineStatusResponse(
        project_id=project["id"],
        status=CANCELLED_STATUS,
        steps=[
            PipelineStepStatus(
                step=s["step"],
                status=s["status"],
                provider=s.get("provider"),
                error_message=s.get("error_message"),
                duration_ms=s.get("duration_ms"),
            )
            for s in steps_res.data
        ],
    )


# ─── 단계별 실행/검토/승인/재생성 엔드포인트 ───


def _get_step_row(
    project_id: int, step: str, supabase: Client
) -> dict:
    """파이프라인 단계 행을 조회한다."""
    if step not in STEP_ORDER:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 단계입니다: {step}. 허용: {', '.join(STEP_ORDER)}",
        )
    res = (
        supabase.table("pipeline_steps")
        .select("*")
        .filter("project_id", "eq", project_id)
        .filter("step", "eq", step)
        .execute()
    )
    if not res.data:
        raise HTTPException(
            status_code=404,
            detail=f"파이프라인 단계를 찾을 수 없습니다: step={step}",
        )
    return res.data[0]


@router.post("/{project_id}/steps/{step}/run", response_model=StepRunResponse)
async def run_step(
    project_id: int,
    step: str,
    body: StepRunRequest,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
    enc: EncryptionService = Depends(get_encryption_service),
):
    """단일 파이프라인 단계를 실행한다."""
    _get_user_project(project_id, user_id, supabase)
    step_row = _get_step_row(project_id, step, supabase)

    if step_row["status"] not in ("pending", "failed"):
        raise HTTPException(
            status_code=409,
            detail=f"단계를 실행할 수 없는 상태입니다: status={step_row['status']}. pending 또는 failed 상태에서만 실행 가능합니다.",
        )

    # 프로바이더 유효성 검증
    allowed = STEP_PROVIDERS.get(step, [])
    if allowed and body.provider not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"이 단계에서 사용할 수 없는 프로바이더입니다: {body.provider}. 허용: {', '.join(allowed)}",
        )

    # API 키가 필요한 프로바이더인지 확인 (무료/로컬 프로바이더 제외)
    FREE_PROVIDERS = {"edgetts", "ollama", "comfyui", "script"}
    if body.provider and body.provider not in FREE_PROVIDERS:
        key_res = (
            supabase.table("api_keys")
            .select("id")
            .filter("user_id", "eq", user_id)
            .filter("provider", "eq", body.provider)
            .execute()
        )
        if not key_res.data:
            raise HTTPException(
                status_code=400,
                detail=f"'{body.provider}' API 키가 등록되지 않았습니다. 설정 페이지에서 API 키를 먼저 등록해 주세요.",
            )

    task_id = dispatch_step(
        project_id=project_id,
        step=step,
        provider=body.provider,
        provider_config=body.config,
        user_id=user_id,
        supabase=supabase,
        enc=enc,
    )

    return StepRunResponse(step=step, status="running")


@router.get("/{project_id}/steps/{step}/output", response_model=StepOutputResponse)
async def get_step_output(
    project_id: int,
    step: str,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    """단계의 생성 결과를 반환한다."""
    _get_user_project(project_id, user_id, supabase)
    step_row = _get_step_row(project_id, step, supabase)

    return StepOutputResponse(
        step=step_row["step"],
        status=step_row["status"],
        output_data=step_row.get("output_data"),
    )


@router.post("/{project_id}/steps/{step}/approve", response_model=StepOutputResponse)
async def approve_step(
    project_id: int,
    step: str,
    body: StepApproveRequest | None = None,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    """단계를 승인하고 다음 단계로 진행 가능하게 한다."""
    _get_user_project(project_id, user_id, supabase)
    step_row = _get_step_row(project_id, step, supabase)

    if step_row["status"] != "awaiting_review":
        raise HTTPException(
            status_code=409,
            detail=f"검토 대기 상태가 아닙니다: status={step_row['status']}",
        )

    update_data: dict = {"status": "approved"}

    # 사용자가 편집한 데이터가 있으면 output_data 업데이트
    if body and body.edited_data:
        update_data["output_data"] = body.edited_data

    supabase.table("pipeline_steps").update(update_data).filter(
        "project_id", "eq", project_id
    ).filter("step", "eq", step).execute()

    # 업데이트된 행 반환
    updated = _get_step_row(project_id, step, supabase)
    return StepOutputResponse(
        step=updated["step"],
        status=updated["status"],
        output_data=updated.get("output_data"),
    )


@router.post("/{project_id}/steps/{step}/reject", response_model=StepOutputResponse)
async def reject_step(
    project_id: int,
    step: str,
    body: StepRejectRequest | None = None,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client),
):
    """단계를 거부하고 재생성 가능하게 리셋한다."""
    _get_user_project(project_id, user_id, supabase)
    step_row = _get_step_row(project_id, step, supabase)

    if step_row["status"] not in ("awaiting_review", "failed"):
        raise HTTPException(
            status_code=409,
            detail=f"거부할 수 없는 상태입니다: status={step_row['status']}",
        )

    supabase.table("pipeline_steps").update(
        {
            "status": "pending",
            "output_data": None,
            "error_message": None,
        }
    ).filter("project_id", "eq", project_id).filter(
        "step", "eq", step
    ).execute()

    updated = _get_step_row(project_id, step, supabase)
    return StepOutputResponse(
        step=updated["step"],
        status=updated["status"],
        output_data=None,
    )
