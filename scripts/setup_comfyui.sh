#!/bin/bash
# ComfyUI + IP-Adapter 설치 스크립트
# Mac Studio M4 Max 64GB 기준
# 총 다운로드: ~12GB (SDXL 6.5GB + IP-Adapter 1.5GB + CLIP ViT-H 3.9GB)

set -e

COMFYUI_DIR="${COMFYUI_DIR:-$HOME/ComfyUI}"
MODELS_DIR="$COMFYUI_DIR/models"

echo "=== ComfyUI + IP-Adapter 설치 ==="
echo "설치 경로: $COMFYUI_DIR"
echo ""

# 0. Python 3.10+ 탐색 및 설정
echo "[0/5] Python 3.10+ 탐색 중..."
PYTHON_BIN=""

# 탐색 순서: python3.12, python3.11, python3.10, python3 (버전 체크)
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" >/dev/null 2>&1; then
        VERSION=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        MAJOR=$(echo "$VERSION" | cut -d. -f1)
        MINOR=$(echo "$VERSION" | cut -d. -f2)
        
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_BIN=$(command -v "$cmd")
            echo "  발견된 호환 Python: $PYTHON_BIN (버전 $VERSION)"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: Python 3.10 이상이 필요합니다. (현재 시스템 Python 3.9 이하)"
    echo "설치 방법: brew install python@3.11"
    exit 1
fi

# 1. ComfyUI 클론
if [ -d "$COMFYUI_DIR" ]; then
    echo "[SKIP] ComfyUI가 이미 존재합니다: $COMFYUI_DIR"
else
    echo "[1/5] ComfyUI 클론 중..."
    git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFYUI_DIR"
fi

# 2. Virtual Environment 및 의존성 설치
echo "[2/5] Python 가상 환경(venv) 및 의존성 설치 중..."
cd "$COMFYUI_DIR"

if [ ! -d "venv" ]; then
    echo "  가상 환경 생성 중..."
    "$PYTHON_BIN" -m venv venv
fi

echo "  의존성 설치 중 (pip install)..."
./venv/bin/python -m pip install --upgrade pip --quiet
./venv/bin/python -m pip install -r requirements.txt --quiet

# 3. ComfyUI-IPAdapter-plus 커스텀 노드 설치
IPADAPTER_DIR="$COMFYUI_DIR/custom_nodes/ComfyUI_IPAdapter_plus"
if [ -d "$IPADAPTER_DIR" ]; then
    echo "[SKIP] IP-Adapter 노드가 이미 존재합니다"
else
    echo "[3/5] IP-Adapter 커스텀 노드 설치 중..."
    cd "$COMFYUI_DIR/custom_nodes"
    git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git
fi

# 4. 모델 다운로드
echo "[4/5] 모델 다운로드 중 (약 12GB)..."

# SDXL Base 1.0
SDXL_PATH="$MODELS_DIR/checkpoints/sd_xl_base_1.0.safetensors"
if [ -f "$SDXL_PATH" ]; then
    echo "  [SKIP] SDXL Base 1.0 이미 존재"
else
    echo "  다운로드: SDXL Base 1.0 (~6.5GB)..."
    curl -L -o "$SDXL_PATH" \
        "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors"
fi

# IP-Adapter Plus SDXL
IPADAPTER_PATH="$MODELS_DIR/ipadapter/ip-adapter-plus_sdxl_vit-h.safetensors"
mkdir -p "$MODELS_DIR/ipadapter"
if [ -f "$IPADAPTER_PATH" ]; then
    echo "  [SKIP] IP-Adapter Plus 이미 존재"
else
    echo "  다운로드: IP-Adapter Plus SDXL (~1.5GB)..."
    curl -L -o "$IPADAPTER_PATH" \
        "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors"
fi

# CLIP ViT-H
CLIP_PATH="$MODELS_DIR/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"
mkdir -p "$MODELS_DIR/clip_vision"
if [ -f "$CLIP_PATH" ]; then
    echo "  [SKIP] CLIP ViT-H 이미 존재"
else
    echo "  다운로드: CLIP ViT-H (~3.9GB)..."
    curl -L -o "$CLIP_PATH" \
        "https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors"
fi

# 5. 완료
echo ""
echo "=== 설치 완료 ==="
echo ""
echo "ComfyUI 시작 방법:"
echo "  cd $COMFYUI_DIR"
echo "  ./venv/bin/python main.py --listen 127.0.0.1 --port 8188"
echo ""
echo "AutoTube 설정:"
echo "  설정 > ComfyUI URL: http://127.0.0.1:8188"
echo ""
echo "참고: Apple Silicon MPS 가속이 자동으로 활성화됩니다."
