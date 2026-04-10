from app.celery_app import celery_app as celery

# 워커 모듈을 임포트하여 Celery에 태스크를 등록한다.
# 이 임포트가 없으면 워커가 태스크를 인식하지 못해 "unregistered task" 에러가 발생한다.
from app.workers import script  # noqa: F401
from app.workers import tts  # noqa: F401
from app.workers import images  # noqa: F401
from app.workers import video  # noqa: F401
from app.workers import video_gen  # noqa: F401
from app.workers import subtitle  # noqa: F401
from app.workers import metadata  # noqa: F401
from app.workers import bgm  # noqa: F401
from app.workers import seo  # noqa: F401
from app.workers import sns  # noqa: F401
from app.workers import thumbnail  # noqa: F401
from app.workers import audio_postprocess  # noqa: F401
from app.workers import youtube_upload  # noqa: F401
from app.services import task_callback  # noqa: F401

__all__ = ["celery"]
