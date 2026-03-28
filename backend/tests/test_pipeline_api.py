import json

from app.models.project import PipelineStep
from app.services.progress import PipelineProgress


# --- API Tests ---


def test_start_pipeline(client, test_project, test_user):
    response = client.post(
        f"/api/pipeline/{test_project.id}/start",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["project_id"] == test_project.id
    assert "video" in data["active_steps"]
    assert "script" in data["active_steps"]
    assert "tts" in data["active_steps"]


def test_start_pipeline_project_not_found(client, test_user, test_db):
    nonexistent_id = 99999
    response = client.post(
        f"/api/pipeline/{nonexistent_id}/start",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 404
    assert "프로젝트를 찾을 수 없습니다" in response.json()["detail"]


def test_start_pipeline_no_config(client, test_db, test_user):
    """pipeline_config가 비어있어도 video step은 포함된다 (REQUIRED_STEPS)."""
    from app.models.project import Project

    project = Project(
        user_id=test_user.id,
        title="No Config",
        type="shorts",
        topic="test topic",
        pipeline_config={},
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)

    response = client.post(
        f"/api/pipeline/{project.id}/start",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert "video" in data["active_steps"]


def test_get_pipeline_status(client, test_project, test_user, test_db):
    # 먼저 파이프라인 시작
    client.post(
        f"/api/pipeline/{test_project.id}/start",
        headers={"X-User-Id": test_user.id},
    )

    response = client.get(
        f"/api/pipeline/{test_project.id}/status",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == test_project.id
    assert data["status"] == "running"
    assert len(data["steps"]) > 0
    step_names = [s["step"] for s in data["steps"]]
    assert "video" in step_names


def test_get_pipeline_status_not_found(client, test_user, test_db):
    nonexistent_id = 99999
    response = client.get(
        f"/api/pipeline/{nonexistent_id}/status",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 404


def test_cancel_pipeline(client, test_project, test_user, test_db):
    # 파이프라인 시작
    client.post(
        f"/api/pipeline/{test_project.id}/start",
        headers={"X-User-Id": test_user.id},
    )

    # running 상태의 step 하나를 만든다
    running_step = (
        test_db.query(PipelineStep)
        .filter_by(project_id=test_project.id)
        .first()
    )
    running_step.status = "running"
    test_db.commit()

    # 취소
    response = client.post(
        f"/api/pipeline/{test_project.id}/cancel",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"

    # running이었던 step이 cancelled로 변경되었는지 확인
    cancelled_steps = [s for s in data["steps"] if s["status"] == "cancelled"]
    assert len(cancelled_steps) >= 1


def test_cancel_pipeline_not_found(client, test_user, test_db):
    nonexistent_id = 99999
    response = client.post(
        f"/api/pipeline/{nonexistent_id}/cancel",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 404


def test_start_pipeline_already_running(client, test_project, test_user, test_db):
    # 첫 번째 시작
    response = client.post(
        f"/api/pipeline/{test_project.id}/start",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200

    # 두 번째 시작 시도 → 409
    response = client.post(
        f"/api/pipeline/{test_project.id}/start",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 409
    assert "이미 실행 중" in response.json()["detail"]


# --- PipelineProgress Unit Tests ---


def test_progress_publish_and_get():
    tracker = PipelineProgress()
    event = tracker.publish(project_id=1, step="script", status="running", detail="생성 중")

    assert event["project_id"] == 1
    assert event["step"] == "script"
    assert event["status"] == "running"
    assert event["detail"] == "생성 중"
    assert "timestamp" in event

    events = tracker.get_events(project_id=1)
    assert len(events) == 1
    assert events[0] == event

    # 다른 프로젝트는 비어있어야 함
    assert tracker.get_events(project_id=999) == []


def test_progress_format_sse():
    tracker = PipelineProgress()
    event = tracker.publish(project_id=1, step="tts", status="completed")

    sse = tracker.format_sse(event)
    assert sse.startswith("data: ")
    assert sse.endswith("\n\n")

    parsed = json.loads(sse.removeprefix("data: ").strip())
    assert parsed["step"] == "tts"
    assert parsed["status"] == "completed"


def test_progress_clear():
    tracker = PipelineProgress()
    tracker.publish(project_id=1, step="script", status="running")
    tracker.publish(project_id=1, step="tts", status="pending")
    assert len(tracker.get_events(project_id=1)) == 2

    tracker.clear(project_id=1)
    assert tracker.get_events(project_id=1) == []

    # 존재하지 않는 프로젝트 clear는 에러 없이 통과
    tracker.clear(project_id=999)
