from __future__ import annotations

import asyncio
import os

import httpx

from app.celery_app import celery_app
from app.services.storage import (
    StorageService,
    build_storage_key,
    save_local,
    save_to_output_dir,
)

try:
    import edge_tts

    EDGE_TTS_AVAILABLE = True
except ImportError:
    edge_tts = None  # type: ignore[assignment]
    EDGE_TTS_AVAILABLE = False

ELEVENLABS_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
OPENAI_DEFAULT_VOICE = "alloy"
EDGE_TTS_DEFAULT_VOICE = "ko-KR-SunHiNeural"
EDGE_TTS_VOICES: dict[str, str] = {
    "ko": "ko-KR-SunHiNeural",
    "en": "en-US-AriaNeural",
    "ja": "ja-JP-NanamiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
}
MAX_TTS_CHUNK_LENGTH = 4000
API_TIMEOUT_SECONDS = 120.0
AUDIO_FILENAME = "audio.mp3"
AUDIO_CONTENT_TYPE = "audio/mpeg"


def _get_storage() -> StorageService | None:
    """R2 스토리지 서비스를 환경변수에서 초기화. 설정 없으면 None."""
    endpoint = os.environ.get("R2_ENDPOINT")
    access_key = os.environ.get("R2_ACCESS_KEY")
    secret_key = os.environ.get("R2_SECRET_KEY")
    bucket = os.environ.get("R2_BUCKET")
    if not all([endpoint, access_key, secret_key, bucket]):
        return None
    return StorageService(endpoint, access_key, secret_key, bucket)


def _upload_audio(project_id: int, audio_data: bytes) -> str | None:
    """오디오를 저장하고 URL을 반환. R2 설정 시 R2, 미설정 시 로컬 저장.
    동시에 사용자 출력 디렉토리에도 복사한다."""
    key = build_storage_key(project_id, "tts", AUDIO_FILENAME)
    storage = _get_storage()
    if storage is not None:
        url = storage.upload_file(key, audio_data, AUDIO_CONTENT_TYPE)
    else:
        url = save_local(key, audio_data)
    # 사용자 출력 디렉토리에도 저장
    save_to_output_dir(project_id, AUDIO_FILENAME, audio_data)
    return url


def build_tts_request(
    text: str,
    provider: str,
    api_key: str,
    voice_id: str | None = None,
) -> dict:
    if provider == "elevenlabs":
        vid = voice_id or ELEVENLABS_DEFAULT_VOICE_ID
        return {
            "url": f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
            "headers": {
                "xi-api-key": api_key,
                "Content-Type": "application/json",
            },
            "json": {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
        }
    elif provider == "openai":
        return {
            "url": "https://api.openai.com/v1/audio/speech",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            "json": {
                "model": "tts-1",
                "input": text,
                "voice": voice_id or OPENAI_DEFAULT_VOICE,
                "response_format": "mp3",
            },
        }
    elif provider == "edgetts":
        return None  # Edge TTS는 HTTP API가 아닌 로컬 라이브러리 → 별도 처리
    else:
        raise ValueError(
            f"지원하지 않는 TTS provider입니다: {provider}. "
            "'elevenlabs', 'openai' 또는 'edgetts'를 사용하세요."
        )


def split_text_for_tts(text: str) -> list[str]:
    if len(text) <= MAX_TTS_CHUNK_LENGTH:
        return [text]

    chunks: list[str] = []
    sentences = text.replace("! ", "!\n").replace("? ", "?\n").replace(". ", ".\n").split("\n")
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(current_chunk) + len(sentence) + 1 > MAX_TTS_CHUNK_LENGTH:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk = f"{current_chunk} {sentence}" if current_chunk else sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def _speed_to_edge_tts_rate(speed: float) -> str:
    """Convert speed float (0.5-2.0) to Edge TTS rate string (e.g. '+20%', '-30%')."""
    percentage = round((speed - 1.0) * 100)
    if percentage >= 0:
        return f"+{percentage}%"
    return f"{percentage}%"


def _generate_edge_tts(
    text: str,
    voice: str,
    speed: float = 1.0,
) -> bytes:
    """Run edge-tts in a synchronous context via asyncio."""
    if not EDGE_TTS_AVAILABLE:
        raise ValueError(
            "edge-tts 패키지가 설치되지 않았습니다. "
            "'pip install edge-tts'로 설치하세요."
        )

    rate = _speed_to_edge_tts_rate(speed)

    async def _run() -> bytes:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        audio_chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        return b"".join(audio_chunks)

    return asyncio.run(_run())


@celery_app.task(name="pipeline.generate_tts")
def generate_tts_task(
    project_id: int,
    text: str,
    provider: str,
    api_key: str | None = None,
    voice_id: str | None = None,
    speed: float = 1.0,
    emotion: str = "normal",
) -> dict:
    # Edge TTS: 로컬 라이브러리 직접 호출 (API 키 불필요)
    if provider == "edgetts":
        voice = voice_id or EDGE_TTS_DEFAULT_VOICE
        audio_data = _generate_edge_tts(text, voice, speed=speed)
        audio_url = _upload_audio(project_id, audio_data)
        return {
            "audio_url": audio_url,
            "audio_size": len(audio_data),
            "chunk_count": 1,
            "provider": "edgetts",
        }

    # 유료 TTS: HTTP API 호출
    chunks = split_text_for_tts(text)
    audio_parts: list[bytes] = []

    for chunk in chunks:
        request = build_tts_request(chunk, provider, api_key or "", voice_id)
        # OpenAI TTS: speed 파라미터 지원
        if provider == "openai" and request and speed != 1.0:
            request["json"]["speed"] = speed
        response = httpx.post(
            request["url"],
            headers=request["headers"],
            json=request["json"],
            timeout=API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        audio_parts.append(response.content)

    combined_audio = b"".join(audio_parts)
    audio_url = _upload_audio(project_id, combined_audio)

    return {
        "audio_url": audio_url,
        "audio_size": len(combined_audio),
        "chunk_count": len(chunks),
        "provider": provider,
    }
