import json
from datetime import datetime, timezone

CHANNEL_PREFIX = "pipeline:progress:"


class PipelineProgress:
    """Tracks pipeline step progress. In production, backed by Redis pub/sub."""

    def __init__(self):
        self._events: dict[int, list[dict]] = {}

    def publish(self, project_id: int, step: str, status: str, detail: str = "") -> dict:
        """Publish a progress event. Returns the event dict."""
        event = {
            "project_id": project_id,
            "step": step,
            "status": status,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if project_id not in self._events:
            self._events[project_id] = []
        self._events[project_id].append(event)
        return event

    def get_events(self, project_id: int) -> list[dict]:
        """Get all events for a project."""
        return list(self._events.get(project_id, []))

    def clear(self, project_id: int) -> None:
        """Clear events for a project."""
        self._events.pop(project_id, None)

    def format_sse(self, event: dict) -> str:
        """Format event as SSE data line."""
        return f"data: {json.dumps(event)}\n\n"


# Singleton instance
progress_tracker = PipelineProgress()
