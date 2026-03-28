#!/bin/bash
# AutoTube - 서비스 종료 / Stop all services
# Usage: ./stop.sh        (한국어)
#        ./stop.sh --en   (English)

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$ROOT_DIR/.autotube.pids"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Language ──────────────────────────────────────────────
LANG_FLAG="${1:-ko}"
if [ "$LANG_FLAG" = "--en" ] || [ "$LANG_FLAG" = "en" ]; then
  L_TITLE="AutoTube - Stopping services..."
  L_STOPPED="stopped"
  L_NOT_RUNNING="not running"
  L_NO_PID="No PID file found. Trying to find processes..."
  L_ALL_STOPPED="All services stopped."
else
  L_TITLE="AutoTube - 서비스 종료 중..."
  L_STOPPED="종료됨"
  L_NOT_RUNNING="실행 중 아님"
  L_NO_PID="PID 파일 없음. 프로세스를 직접 찾는 중..."
  L_ALL_STOPPED="모든 서비스가 종료되었습니다."
fi

echo ""
echo "  $L_TITLE"
echo "  ================================"
echo ""

kill_proc() {
  local name="$1"
  local pid="$2"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null
    wait "$pid" 2>/dev/null
    echo -e "  $name ${GREEN}$L_STOPPED${NC} (PID $pid)"
  else
    echo -e "  $name ${YELLOW}$L_NOT_RUNNING${NC}"
  fi
}

if [ -f "$PID_FILE" ]; then
  source "$PID_FILE"
  kill_proc "Frontend " "$FRONTEND_PID"
  kill_proc "Celery   " "$CELERY_PID"
  kill_proc "Backend  " "$BACKEND_PID"
  kill_proc "ComfyUI  " "$COMFYUI_PID"
  rm -f "$PID_FILE"
else
  echo -e "  ${YELLOW}$L_NO_PID${NC}"
  echo ""

  # Fallback: kill by port/name
  pkill -f "uvicorn app.main:app" 2>/dev/null && echo -e "  Backend  ${GREEN}$L_STOPPED${NC}" || echo -e "  Backend  ${YELLOW}$L_NOT_RUNNING${NC}"
  pkill -f "celery -A app.workers" 2>/dev/null && echo -e "  Celery   ${GREEN}$L_STOPPED${NC}" || echo -e "  Celery   ${YELLOW}$L_NOT_RUNNING${NC}"
  pkill -f "next dev" 2>/dev/null && echo -e "  Frontend ${GREEN}$L_STOPPED${NC}" || echo -e "  Frontend ${YELLOW}$L_NOT_RUNNING${NC}"
  pkill -f "main.py --listen 127.0.0.1 --port 8188" 2>/dev/null && echo -e "  ComfyUI  ${GREEN}$L_STOPPED${NC}" || echo -e "  ComfyUI  ${YELLOW}$L_NOT_RUNNING${NC}"
fi

# Clean up log files
rm -f "$ROOT_DIR/.backend.log" "$ROOT_DIR/.celery.log" "$ROOT_DIR/.frontend.log" "$ROOT_DIR/.comfyui.log"

echo ""
echo "  ================================"
echo -e "  ${GREEN}$L_ALL_STOPPED${NC}"
echo ""
