# AutoTube Phase 1 (MVP) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a working YouTube video automation SaaS MVP — users input a topic, configure pipeline steps, and generate downloadable Shorts videos.

**Architecture:** Next.js 16 frontend on Vercel communicates via REST API with a FastAPI backend on Railway. Celery workers process video generation pipeline asynchronously. Redis handles task queue and SSE pub/sub. PostgreSQL stores all structured data. Cloudflare R2 stores generated files.

**Tech Stack:** Next.js 16, TypeScript, shadcn/ui, Tailwind CSS, Clerk, FastAPI, Celery, Redis, PostgreSQL, SQLAlchemy, MoviePy, FFmpeg, Pillow, cryptography (AES-256-GCM)

---

## Phase 1 Scope

MVP focuses on:
- Shorts video generation only (9:16, 30-60s)
- 6 pipeline steps: Script → TTS → Images → Video → Subtitle → Metadata
- No YouTube upload (download only)
- No thumbnails (Phase 2)
- No billing/Stripe (Phase 2) — all users get Free tier
- Local Clerk auth
- API key management (encrypted)
- Real-time pipeline progress (SSE)

---

## Task 1: Project Scaffolding — Backend (Python)

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/.env.example`
- Create: `backend/Dockerfile`

**Step 1: Initialize Python project with pyproject.toml**

```toml
[project]
name = "autotube-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.14.0",
    "psycopg2-binary>=2.9.0",
    "celery[redis]>=5.4.0",
    "redis>=5.0.0",
    "httpx>=0.28.0",
    "python-multipart>=0.0.18",
    "cryptography>=44.0.0",
    "moviepy>=2.1.0",
    "Pillow>=11.0.0",
    "boto3>=1.36.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.25.0",
    "httpx>=0.28.0",
    "ruff>=0.9.0",
]
```

**Step 2: Create config.py with pydantic-settings**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://localhost:5432/autotube"
    redis_url: str = "redis://localhost:6379/0"
    r2_endpoint: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_bucket: str = "autotube"
    encryption_master_key: str = ""
    clerk_secret_key: str = ""
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env"}


settings = Settings()
```

**Step 3: Create main.py with FastAPI app**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="AutoTube API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 4: Create .env.example**

```
DATABASE_URL=postgresql://localhost:5432/autotube
REDIS_URL=redis://localhost:6379/0
R2_ENDPOINT=
R2_ACCESS_KEY=
R2_SECRET_KEY=
R2_BUCKET=autotube
ENCRYPTION_MASTER_KEY=
CLERK_SECRET_KEY=
CORS_ORIGINS=["http://localhost:3000"]
```

**Step 5: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 6: Verify**

Run: `cd backend && pip install -e ".[dev]" && uvicorn app.main:app --reload`
Expected: Server starts, `GET /health` returns `{"status": "ok"}`

**Step 7: Commit**

```bash
git add backend/
git commit -m "feat: scaffold FastAPI backend with config and Docker"
```

---

## Task 2: Project Scaffolding — Frontend (Next.js)

**Files:**
- Create: `frontend/` (via `npx create-next-app@latest`)
- Modify: `frontend/package.json`
- Create: `frontend/.env.example`

**Step 1: Scaffold Next.js 16 project**

Run:
```bash
npx create-next-app@latest frontend \
  --typescript --tailwind --eslint --app \
  --src-dir --import-alias "@/*" --turbopack
```

**Step 2: Install dependencies**

Run:
```bash
cd frontend
npm install @clerk/nextjs
npx shadcn@latest init -d
```

**Step 3: Create .env.example**

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/login
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/signup
```

**Step 4: Verify**

Run: `npm run dev`
Expected: Next.js dev server starts at http://localhost:3000

**Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Next.js 16 frontend with shadcn/ui and Clerk"
```

---

## Task 3: Database Models & Migrations

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/api_key.py`
- Create: `backend/app/models/project.py`
- Create: `backend/app/database.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `tests/test_models.py`

**Step 1: Write failing test for User model**

```python
# backend/tests/test_models.py
from app.models.user import User


def test_user_model_has_required_fields():
    user = User(
        id="user_123",
        email="test@example.com",
        name="Test User",
        plan="free",
    )
    assert user.id == "user_123"
    assert user.email == "test@example.com"
    assert user.plan == "free"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models.py::test_user_model_has_required_fields -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.models'`

**Step 3: Create database.py**

```python
# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 4: Create all models**

```python
# backend/app/models/__init__.py
from app.models.user import User
from app.models.api_key import ApiKey
from app.models.project import Project, PipelineStep, Asset

__all__ = ["User", "ApiKey", "Project", "PipelineStep", "Asset"]
```

```python
# backend/app/models/user.py
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)
    plan: Mapped[str] = mapped_column(String, default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="user")
    projects: Mapped[list["Project"]] = relationship(back_populates="user")
```

```python
# backend/app/models/api_key.py
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, ForeignKey, LargeBinary, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    encrypted_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    tag: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="api_keys")
```

```python
# backend/app/models/project.py
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, JSON, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # shorts | longform
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="draft")
    pipeline_config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="projects")
    steps: Mapped[list["PipelineStep"]] = relationship(back_populates="project")
    assets: Mapped[list["Asset"]] = relationship(back_populates="project")


class PipelineStep(Base):
    __tablename__ = "pipeline_steps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    step: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_url: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="steps")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    step: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    storage_url: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="assets")
```

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: PASS

**Step 6: Initialize Alembic and create first migration**

Run:
```bash
cd backend
alembic init alembic
# Edit alembic/env.py to import Base and models
alembic revision --autogenerate -m "initial models"
alembic upgrade head
```

**Step 7: Commit**

```bash
git add backend/app/models/ backend/app/database.py backend/alembic* backend/tests/
git commit -m "feat: add database models and initial migration"
```

---

## Task 4: API Key Encryption Service

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/encryption.py`
- Create: `backend/tests/test_encryption.py`

**Step 1: Write failing test**

```python
# backend/tests/test_encryption.py
import os

from app.services.encryption import EncryptionService


def test_encrypt_decrypt_roundtrip():
    master_key = os.urandom(32).hex()
    svc = EncryptionService(master_key)

    plaintext = "sk-test-api-key-1234567890"
    encrypted, nonce, tag = svc.encrypt(plaintext)

    assert encrypted != plaintext.encode()
    assert svc.decrypt(encrypted, nonce, tag) == plaintext


def test_mask_key():
    assert EncryptionService.mask("sk-proj-abcdefghijklmnop") == "sk-p...mnop"
    assert EncryptionService.mask("short") == "s...ort"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_encryption.py -v`
Expected: FAIL

**Step 3: Implement encryption service**

```python
# backend/app/services/encryption.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    def __init__(self, master_key_hex: str):
        self._key = bytes.fromhex(master_key_hex)
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> tuple[bytes, bytes, bytes]:
        import os

        nonce = os.urandom(12)
        ciphertext_and_tag = self._aesgcm.encrypt(nonce, plaintext.encode(), None)
        ciphertext = ciphertext_and_tag[:-16]
        tag = ciphertext_and_tag[-16:]
        return ciphertext, nonce, tag

    def decrypt(self, ciphertext: bytes, nonce: bytes, tag: bytes) -> str:
        plaintext = self._aesgcm.decrypt(nonce, ciphertext + tag, None)
        return plaintext.decode()

    @staticmethod
    def mask(key: str) -> str:
        if len(key) <= 8:
            return f"{key[0]}...{key[-3:]}"
        return f"{key[:4]}...{key[-4:]}"
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_encryption.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/ backend/tests/test_encryption.py
git commit -m "feat: add AES-256-GCM encryption service for API keys"
```

---

## Task 5: API Key CRUD Endpoints

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/api_keys.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/api_key.py`
- Create: `backend/tests/test_api_keys.py`

**Step 1: Write failing test**

```python
# backend/tests/test_api_keys.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_api_key(test_db, test_user):
    response = client.post(
        "/api/settings/api-keys",
        json={"provider": "openai", "key": "sk-test-key-123"},
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "openai"
    assert "****" in data["masked_key"]
    assert "key" not in data


def test_list_api_keys(test_db, test_user):
    response = client.get(
        "/api/settings/api-keys",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_delete_api_key(test_db, test_user, test_api_key):
    response = client.delete(
        f"/api/settings/api-keys/{test_api_key.id}",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 204
```

**Step 2: Create Pydantic schemas**

```python
# backend/app/schemas/api_key.py
from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    provider: str
    key: str


class ApiKeyResponse(BaseModel):
    id: int
    provider: str
    masked_key: str
    is_valid: bool

    model_config = {"from_attributes": True}
```

**Step 3: Implement router**

```python
# backend/app/routers/api_keys.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse
from app.services.encryption import EncryptionService

router = APIRouter(prefix="/api/settings/api-keys", tags=["api-keys"])

VALID_PROVIDERS = {"openai", "claude", "elevenlabs", "gemini", "pexels", "youtube"}


def get_encryption_service() -> EncryptionService:
    return EncryptionService(settings.encryption_master_key)


@router.post("", status_code=201, response_model=ApiKeyResponse)
async def create_api_key(
    body: ApiKeyCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    enc: EncryptionService = Depends(get_encryption_service),
):
    if body.provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 provider입니다: {body.provider}. 지원 목록: {', '.join(sorted(VALID_PROVIDERS))}",
        )

    existing = db.query(ApiKey).filter_by(user_id=user_id, provider=body.provider).first()
    if existing:
        db.delete(existing)

    encrypted, nonce, tag = enc.encrypt(body.key)
    api_key = ApiKey(
        user_id=user_id,
        provider=body.provider,
        encrypted_key=encrypted,
        nonce=nonce,
        tag=tag,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return ApiKeyResponse(
        id=api_key.id,
        provider=api_key.provider,
        masked_key=EncryptionService.mask(body.key),
        is_valid=api_key.is_valid,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    keys = db.query(ApiKey).filter_by(user_id=user_id).all()
    return [
        ApiKeyResponse(
            id=k.id,
            provider=k.provider,
            masked_key="****",
            is_valid=k.is_valid,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(
    key_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    key = db.query(ApiKey).filter_by(id=key_id, user_id=user_id).first()
    if not key:
        raise HTTPException(
            status_code=404,
            detail=f"API 키를 찾을 수 없습니다: id={key_id}",
        )
    db.delete(key)
    db.commit()
```

**Step 4: Register router in main.py, run tests**

Run: `cd backend && pytest tests/test_api_keys.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/routers/ backend/app/schemas/ backend/tests/test_api_keys.py
git commit -m "feat: add API key CRUD endpoints with encryption"
```

---

## Task 6: Project CRUD Endpoints

**Files:**
- Create: `backend/app/routers/projects.py`
- Create: `backend/app/schemas/project.py`
- Create: `backend/tests/test_projects.py`

**Step 1: Write failing test**

```python
# backend/tests/test_projects.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_project(test_db, test_user):
    response = client.post(
        "/api/projects",
        json={
            "title": "Test Video",
            "type": "shorts",
            "topic": "5 surprising facts about coffee",
            "pipeline_config": {
                "script": True,
                "tts": True,
                "images": True,
                "video": True,
                "subtitle": True,
                "metadata": True,
            },
        },
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Video"
    assert data["type"] == "shorts"
    assert data["status"] == "draft"


def test_list_projects(test_db, test_user):
    response = client.get(
        "/api/projects",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200


def test_get_project(test_db, test_user, test_project):
    response = client.get(
        f"/api/projects/{test_project.id}",
        headers={"X-User-Id": test_user.id},
    )
    assert response.status_code == 200
    assert response.json()["id"] == test_project.id
```

**Step 2: Implement schemas and router (same pattern as Task 5)**

**Step 3: Run tests, verify pass**

**Step 4: Commit**

```bash
git add backend/app/routers/projects.py backend/app/schemas/project.py backend/tests/test_projects.py
git commit -m "feat: add project CRUD endpoints"
```

---

## Task 7: Celery Setup + Pipeline Orchestrator

**Files:**
- Create: `backend/app/celery_app.py`
- Create: `backend/app/services/pipeline.py`
- Create: `backend/tests/test_pipeline.py`

**Step 1: Write failing test**

```python
# backend/tests/test_pipeline.py
from app.services.pipeline import PipelineOrchestrator


def test_build_step_chain_all_enabled():
    config = {
        "script": True,
        "tts": True,
        "images": True,
        "video": True,
        "subtitle": True,
        "metadata": True,
    }
    orchestrator = PipelineOrchestrator(config)
    steps = orchestrator.get_active_steps()
    assert steps == ["script", "tts", "images", "video", "subtitle", "metadata"]


def test_build_step_chain_partial():
    config = {
        "script": False,
        "tts": True,
        "images": False,
        "video": True,
        "subtitle": False,
        "metadata": True,
    }
    orchestrator = PipelineOrchestrator(config)
    steps = orchestrator.get_active_steps()
    assert steps == ["tts", "video", "metadata"]
    assert "video" in steps  # always required


def test_video_step_always_included():
    config = {"script": False, "tts": False, "images": False, "video": False, "subtitle": False, "metadata": False}
    orchestrator = PipelineOrchestrator(config)
    steps = orchestrator.get_active_steps()
    assert "video" in steps
```

**Step 2: Create Celery app**

```python
# backend/app/celery_app.py
from celery import Celery

from app.config import settings

celery_app = Celery(
    "autotube",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
```

**Step 3: Implement pipeline orchestrator**

```python
# backend/app/services/pipeline.py
STEP_ORDER = ["script", "tts", "images", "video", "subtitle", "metadata"]
REQUIRED_STEPS = {"video"}


class PipelineOrchestrator:
    def __init__(self, config: dict[str, bool]):
        self._config = config

    def get_active_steps(self) -> list[str]:
        active = []
        for step in STEP_ORDER:
            if step in REQUIRED_STEPS or self._config.get(step, False):
                active.append(step)
        return active
```

**Step 4: Run tests, verify pass**

Run: `cd backend && pytest tests/test_pipeline.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/celery_app.py backend/app/services/pipeline.py backend/tests/test_pipeline.py
git commit -m "feat: add Celery setup and pipeline orchestrator"
```

---

## Task 8: Pipeline Step Workers — Script Generation

**Files:**
- Create: `backend/app/workers/__init__.py`
- Create: `backend/app/workers/script.py`
- Create: `backend/tests/test_worker_script.py`

**Step 1: Write failing test**

```python
# backend/tests/test_worker_script.py
import pytest

from app.workers.script import generate_script_prompt, parse_script_response


def test_generate_script_prompt_shorts():
    prompt = generate_script_prompt(
        topic="5 surprising facts about coffee",
        video_type="shorts",
        language="ko",
    )
    assert "coffee" in prompt
    assert "30-60" in prompt or "shorts" in prompt.lower()


def test_parse_script_response():
    raw = "Scene 1: Coffee was discovered by goats.\nScene 2: Finland drinks the most coffee."
    result = parse_script_response(raw)
    assert result["full_text"]
    assert len(result["scenes"]) >= 1
```

**Step 2: Implement script worker**

```python
# backend/app/workers/script.py
import httpx

from app.celery_app import celery_app


def generate_script_prompt(topic: str, video_type: str, language: str = "ko") -> str:
    duration = "30-60초" if video_type == "shorts" else "5-15분"
    scene_count = "3-5" if video_type == "shorts" else "15-25"

    return f"""당신은 YouTube {video_type} 영상 스크립트 작가입니다.

주제: {topic}
길이: {duration}
장면 수: {scene_count}개
언어: {language}

다음 형식으로 스크립트를 작성하세요:
[장면 N]: (화면 설명)
나레이션: (읽을 내용)

주의사항:
- 첫 3초 안에 시청자의 주의를 끌어야 합니다
- 각 장면은 명확한 비주얼 설명을 포함해야 합니다
- 나레이션은 자연스러운 구어체로 작성하세요"""


def parse_script_response(raw_text: str) -> dict:
    lines = raw_text.strip().split("\n")
    scenes = []
    current_scene = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("[장면") or line.startswith("Scene"):
            if current_scene:
                scenes.append(current_scene)
            current_scene = {"visual": line, "narration": ""}
        elif line.startswith("나레이션:") or line.startswith("Narration:"):
            current_scene["narration"] = line.split(":", 1)[1].strip()
        elif current_scene:
            current_scene["narration"] += " " + line

    if current_scene:
        scenes.append(current_scene)

    return {
        "full_text": raw_text,
        "scenes": scenes,
        "scene_count": len(scenes),
    }


@celery_app.task(name="pipeline.generate_script")
def generate_script_task(
    project_id: int,
    topic: str,
    video_type: str,
    api_provider: str,
    api_key: str,
    language: str = "ko",
) -> dict:
    prompt = generate_script_prompt(topic, video_type, language)

    if api_provider == "openai":
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
    elif api_provider == "claude":
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6-20250514",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60.0,
        )
        response.raise_for_status()
        raw = response.json()["content"][0]["text"]
    else:
        raise ValueError(
            f"지원하지 않는 스크립트 API provider입니다: {api_provider}. 'openai' 또는 'claude'를 사용하세요."
        )

    return parse_script_response(raw)
```

**Step 3: Run tests, verify pass**

**Step 4: Commit**

```bash
git add backend/app/workers/ backend/tests/test_worker_script.py
git commit -m "feat: add script generation pipeline step"
```

---

## Task 9: Pipeline Step Workers — TTS

**Files:**
- Create: `backend/app/workers/tts.py`
- Create: `backend/tests/test_worker_tts.py`

**Step 1: Write failing test for TTS config builder**

```python
# backend/tests/test_worker_tts.py
from app.workers.tts import build_tts_request


def test_build_tts_request_elevenlabs():
    req = build_tts_request(
        text="Hello world",
        provider="elevenlabs",
        voice_id="21m00Tcm4TlvDq8ikWAM",
    )
    assert req["url"].startswith("https://api.elevenlabs.io")
    assert req["body"]["text"] == "Hello world"
```

**Step 2: Implement TTS worker**

Worker calls ElevenLabs or OpenAI TTS API, saves MP3 to R2 storage, returns URL.

**Step 3: Run tests, verify pass, commit**

```bash
git commit -m "feat: add TTS pipeline step (ElevenLabs + OpenAI)"
```

---

## Task 10: Pipeline Step Workers — Image Generation

**Files:**
- Create: `backend/app/workers/images.py`
- Create: `backend/tests/test_worker_images.py`

Extracts keywords from script scenes, generates images via Gemini/DALL-E or fetches from Pexels API.

**Commit:** `git commit -m "feat: add image generation pipeline step"`

---

## Task 11: Pipeline Step Workers — Video Composition

**Files:**
- Create: `backend/app/workers/video.py`
- Create: `backend/tests/test_worker_video.py`

Core step: combines audio + images into MP4 using MoviePy + FFmpeg.
- Ken Burns effect (zoom/pan) on images
- Transition effects between scenes
- Audio sync with image timing
- Output: 1080x1920 (shorts) or 1920x1080 (longform)

**Commit:** `git commit -m "feat: add video composition pipeline step"`

---

## Task 12: Pipeline Step Workers — Subtitle + Metadata

**Files:**
- Create: `backend/app/workers/subtitle.py`
- Create: `backend/app/workers/metadata.py`
- Create: `backend/tests/test_worker_subtitle.py`
- Create: `backend/tests/test_worker_metadata.py`

Subtitle: Whisper API for transcription → SRT → burn into video with MoviePy.
Metadata: AI generates SEO-optimized title, description, tags.

**Commit:** `git commit -m "feat: add subtitle and metadata pipeline steps"`

---

## Task 13: Pipeline Execution Endpoint + SSE Progress

**Files:**
- Create: `backend/app/routers/pipeline.py`
- Create: `backend/app/services/progress.py`
- Create: `backend/tests/test_pipeline_api.py`

**Key functionality:**
- `POST /api/pipeline/{project_id}/start` — starts Celery chain
- `GET /api/pipeline/{project_id}/stream` — SSE endpoint for real-time progress
- Each step publishes progress to Redis pub/sub
- Frontend receives step status changes via SSE

**Commit:** `git commit -m "feat: add pipeline execution endpoint with SSE progress"`

---

## Task 14: Storage Service (Cloudflare R2)

**Files:**
- Create: `backend/app/services/storage.py`
- Create: `backend/tests/test_storage.py`

S3-compatible client for R2:
- `upload_file(key, data, content_type)` → URL
- `get_presigned_url(key, expires)` → temporary download URL
- `delete_file(key)`

**Commit:** `git commit -m "feat: add R2 storage service"`

---

## Task 15: Frontend — Auth Layout + Dashboard

**Files:**
- Create: `frontend/src/app/layout.tsx` (modify for Clerk)
- Create: `frontend/src/app/(auth)/login/[[...login]]/page.tsx`
- Create: `frontend/src/app/(auth)/signup/[[...signup]]/page.tsx`
- Create: `frontend/src/app/(dashboard)/dashboard/page.tsx`
- Create: `frontend/src/app/(dashboard)/layout.tsx`
- Create: `frontend/src/lib/api.ts`

Dashboard shows:
- Project list (table with status badges)
- Usage summary (videos generated this month)
- "New Video" CTA button

**Commit:** `git commit -m "feat: add auth pages and dashboard UI"`

---

## Task 16: Frontend — New Project Wizard

**Files:**
- Create: `frontend/src/app/(dashboard)/projects/new/page.tsx`
- Create: `frontend/src/components/wizard/step-type.tsx`
- Create: `frontend/src/components/wizard/step-topic.tsx`
- Create: `frontend/src/components/wizard/step-pipeline.tsx`
- Create: `frontend/src/components/wizard/step-upload.tsx`
- Create: `frontend/src/components/wizard/step-confirm.tsx`

5-step wizard:
1. Video type selection (Shorts/Long-form toggle)
2. Topic input (textarea + optional detailed settings)
3. Pipeline step toggles (ON/OFF switches per step)
4. File upload for OFF steps (drag & drop)
5. Summary + confirm + start generation

**Commit:** `git commit -m "feat: add new project creation wizard"`

---

## Task 17: Frontend — Project Detail + Progress

**Files:**
- Create: `frontend/src/app/(dashboard)/projects/[id]/page.tsx`
- Create: `frontend/src/components/pipeline-progress.tsx`
- Create: `frontend/src/hooks/use-pipeline-sse.ts`

Real-time pipeline visualization:
- Step indicator (icons + status colors)
- Progress bar per step
- SSE hook for live updates
- Result preview (audio player, image gallery, video player)
- Download button for final video

**Commit:** `git commit -m "feat: add project detail page with real-time progress"`

---

## Task 18: Frontend — Settings (API Keys)

**Files:**
- Create: `frontend/src/app/(dashboard)/settings/page.tsx`
- Create: `frontend/src/components/api-key-form.tsx`

API key management UI:
- Provider list with status indicators
- Add/edit/delete keys
- Validation button (test API call)
- Masked display

**Commit:** `git commit -m "feat: add API key settings page"`

---

## Task 19: Integration Test — Full Pipeline

**Files:**
- Create: `backend/tests/test_integration.py`

End-to-end test with mocked external APIs:
1. Create project
2. Start pipeline
3. Verify each step executes in order
4. Verify assets are created
5. Verify final video output

Run: `cd backend && pytest tests/test_integration.py -v`
Expected: PASS

**Commit:** `git commit -m "test: add full pipeline integration test"`

---

## Task 20: Docker Compose + Local Dev Setup

**Files:**
- Create: `docker-compose.yml`
- Create: `Makefile`
- Create: `README.md`

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
    depends_on: [redis, postgres]

  worker:
    build: ./backend
    command: celery -A app.celery_app worker -l info
    env_file: ./backend/.env
    depends_on: [redis, postgres]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: autotube
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
```

**Commit:** `git commit -m "feat: add Docker Compose for local development"`

---

## Summary

| Task | Description | Estimated Steps |
|------|-------------|-----------------|
| 1 | Backend scaffolding | 7 |
| 2 | Frontend scaffolding | 5 |
| 3 | Database models | 7 |
| 4 | Encryption service | 5 |
| 5 | API key endpoints | 5 |
| 6 | Project endpoints | 4 |
| 7 | Celery + orchestrator | 5 |
| 8 | Script worker | 4 |
| 9 | TTS worker | 3 |
| 10 | Image worker | 3 |
| 11 | Video composition | 3 |
| 12 | Subtitle + metadata | 3 |
| 13 | Pipeline API + SSE | 3 |
| 14 | R2 storage service | 3 |
| 15 | Dashboard UI | 3 |
| 16 | New project wizard | 3 |
| 17 | Project detail + progress | 3 |
| 18 | Settings page | 3 |
| 19 | Integration test | 3 |
| 20 | Docker Compose | 3 |
| **Total** | | **~77 steps** |
