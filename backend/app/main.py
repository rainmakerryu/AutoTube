from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import api_keys, assets, pipeline, projects, users
from app.services.storage import MEDIA_ROOT

app = FastAPI(title="AutoTube API", version="0.1.0")

# 로컬 미디어 파일 서빙 (R2 미설정 시 사용)
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")

# CORS middleware must be added before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


app.include_router(api_keys.router)
app.include_router(assets.router)
app.include_router(pipeline.router)
app.include_router(projects.router)
app.include_router(users.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
