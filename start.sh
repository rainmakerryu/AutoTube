#!/bin/bash
# AutoTube - 서비스 시작 / Start all services
# Usage: ./start.sh        (한국어)
#        ./start.sh --en   (English)

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PID_FILE="$ROOT_DIR/.autotube.pids"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── Language ──────────────────────────────────────────────
LANG_FLAG="${1:-ko}"
if [ "$LANG_FLAG" = "--en" ] || [ "$LANG_FLAG" = "en" ]; then
  L_TITLE="AutoTube - Starting services..."
  L_ALREADY="Services may already be running. Run ./stop.sh first."
  L_ALREADY_RUNNING="already running"
  L_STARTED="started"
  L_NOT_INSTALLED="not installed (brew install redis)"
  L_ALL_STARTED="All services started (including ComfyUI)!"
  L_LOGS="Logs:"
  L_STOP="Stop:  ./stop.sh"
else
  L_TITLE="AutoTube - 서비스 시작 중..."
  L_ALREADY="이미 실행 중일 수 있습니다. ./stop.sh 를 먼저 실행하세요."
  L_ALREADY_RUNNING="이미 실행 중"
  L_STARTED="시작됨"
  L_NOT_INSTALLED="not installed (brew install redis)"
  L_ALL_STARTED="모든 서비스가 시작되었습니다 (ComfyUI 포함)!"
  L_LOGS="로그 확인:"
  L_STOP="종료:  ./stop.sh"
fi

echo ""
echo "  $L_TITLE"
echo "  ================================"
echo ""

# Check if already running
if [ -f "$PID_FILE" ]; then
  echo -e "${YELLOW}  $L_ALREADY${NC}"
  exit 1
fi

# ── 1. Redis ──────────────────────────────────────────────
echo -n "  [1/5] Redis...        "
if command -v redis-cli &>/dev/null && redis-cli ping &>/dev/null 2>&1; then
  echo -e "${GREEN}$L_ALREADY_RUNNING${NC}"
else
  if command -v redis-server &>/dev/null; then
    redis-server --daemonize yes --loglevel warning
    sleep 1
    echo -e "${GREEN}$L_STARTED${NC}"
  else
    echo -e "${RED}$L_NOT_INSTALLED${NC}"
    exit 1
  fi
fi

# ── 2. Backend API (FastAPI + Uvicorn) ────────────────────
echo -n "  [2/5] Backend API...  "
cd "$BACKEND_DIR"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
  > "$ROOT_DIR/.backend.log" 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}$L_STARTED (PID $BACKEND_PID, port 8000)${NC}"

# ── 3. Celery Worker ─────────────────────────────────────
echo -n "  [3/5] Celery Worker.. "
celery -A app.workers worker --loglevel=info --concurrency=2 \
  > "$ROOT_DIR/.celery.log" 2>&1 &
CELERY_PID=$!
echo -e "${GREEN}$L_STARTED (PID $CELERY_PID)${NC}"
deactivate

# ── 4. Frontend (Next.js) ────────────────────────────────
echo -n "  [4/5] Frontend...     "
cd "$FRONTEND_DIR"
npm run dev > "$ROOT_DIR/.frontend.log" 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}$L_STARTED (PID $FRONTEND_PID, port 3000)${NC}"

# ── 5. ComfyUI ───────────────────────────────────────────
echo -n "  [5/5] ComfyUI...      "
COMFYUI_PATH="$HOME/ComfyUI"
if [ -d "$COMFYUI_PATH" ] && [ -f "$COMFYUI_PATH/main.py" ]; then
  cd "$COMFYUI_PATH"
  ./venv/bin/python main.py --listen 127.0.0.1 --port 8188 \
    > "$ROOT_DIR/.comfyui.log" 2>&1 &
  COMFYUI_PID=$!
  echo -e "${GREEN}$L_STARTED (PID $COMFYUI_PID, port 8188)${NC}"
else
  COMFYUI_PID=""
  echo -e "${YELLOW}Not found at $COMFYUI_PATH. Skipping.${NC}"
fi

# Save PIDs
cat > "$PID_FILE" <<EOF
BACKEND_PID=$BACKEND_PID
CELERY_PID=$CELERY_PID
FRONTEND_PID=$FRONTEND_PID
COMFYUI_PID=$COMFYUI_PID
EOF

echo ""
echo "  ================================"
echo -e "  ${GREEN}$L_ALL_STARTED${NC}"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  ComfyUI:   http://127.0.0.1:8188"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "  $L_LOGS"
echo "    tail -f .backend.log"
echo "    tail -f .celery.log"
echo "    tail -f .frontend.log"
echo "    tail -f .comfyui.log"
echo ""
echo "  $L_STOP"
echo ""
