"""Celery 태스크 완료/실패 콜백.

워커 태스크 결과를 Supabase에 저장하고 파이프라인 상태를 전환한다.
"""

from datetime import datetime, timezone

from app.celery_app import celery_app
from app.services.pipeline import PipelineOrchestrator
from app.supabase_client import get_supabase_client


def _get_orchestrator(project_id: int) -> tuple[PipelineOrchestrator, dict]:
    """프로젝트 설정에서 PipelineOrchestrator를 생성하여 반환."""
    supabase = get_supabase_client()
    res = (
        supabase.table("projects")
        .select("pipeline_config")
        .filter("id", "eq", project_id)
        .execute()
    )
    config = res.data[0].get("pipeline_config") or {} if res.data else {}
    return PipelineOrchestrator(config), supabase


@celery_app.task(name="pipeline.on_step_complete", ignore_result=True)
def on_step_complete(result: dict, project_id: int, step: str) -> None:
    """Celery 태스크 성공 콜백. link= 으로 연결된다.

    Args:
        result: 이전 태스크의 반환값 (자동 전달).
        project_id: 프로젝트 ID.
        step: 파이프라인 단계 이름.
    """
    orchestrator, supabase = _get_orchestrator(project_id)

    new_status = (
        "awaiting_review" if orchestrator.needs_review(step) else "completed"
    )

    supabase.table("pipeline_steps").update(
        {
            "status": new_status,
            "output_data": result,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    ).filter("project_id", "eq", project_id).filter(
        "step", "eq", step
    ).execute()

    # 검토 불필요 단계는 자동으로 다음 단계 진행
    if new_status == "completed":
        next_step = orchestrator.get_next_step(step)
        if next_step is None:
            # 마지막 단계 완료 → 프로젝트 완료
            supabase.table("projects").update(
                {"status": "completed"}
            ).filter("id", "eq", project_id).execute()


@celery_app.task(name="pipeline.on_step_failed", bind=True, ignore_result=True)
def on_step_failed(self, failed_task_id: str, project_id: int, step: str) -> None:
    """Celery 태스크 실패 콜백. link_error= 로 연결된다.

    Celery link_error 콜백은 실패한 태스크의 ID를 첫 번째 인자로 받는다.
    bind=True이므로 self가 추가된다.

    Args:
        failed_task_id: 실패한 태스크의 Celery task ID.
        project_id: 프로젝트 ID.
        step: 파이프라인 단계 이름.
    """
    supabase = get_supabase_client()

    # 실패한 태스크의 결과에서 에러 메시지를 가져온다.
    result = self.app.AsyncResult(failed_task_id)
    try:
        error_message = str(result.result) if result.result else "알 수 없는 오류가 발생했습니다."
    except Exception:
        error_message = "알 수 없는 오류가 발생했습니다."

    supabase.table("pipeline_steps").update(
        {
            "status": "failed",
            "error_message": error_message,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    ).filter("project_id", "eq", project_id).filter(
        "step", "eq", step
    ).execute()
