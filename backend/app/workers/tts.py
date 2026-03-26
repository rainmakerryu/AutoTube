import httpx

from app.celery_app import celery_app

ELEVENLABS_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
OPENAI_DEFAULT_VOICE = "alloy"
MAX_TTS_CHUNK_LENGTH = 4000
API_TIMEOUT_SECONDS = 120.0


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
    else:
        raise ValueError(
            f"지원하지 않는 TTS provider입니다: {provider}. "
            "'elevenlabs' 또는 'openai'를 사용하세요."
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


@celery_app.task(name="pipeline.generate_tts")
def generate_tts_task(
    project_id: int,
    text: str,
    provider: str,
    api_key: str,
    voice_id: str | None = None,
) -> dict:
    chunks = split_text_for_tts(text)
    audio_parts: list[bytes] = []

    for chunk in chunks:
        request = build_tts_request(chunk, provider, api_key, voice_id)
        response = httpx.post(
            request["url"],
            headers=request["headers"],
            json=request["json"],
            timeout=API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        audio_parts.append(response.content)

    combined_audio = b"".join(audio_parts)

    return {
        "audio_size": len(combined_audio),
        "chunk_count": len(chunks),
        "provider": provider,
    }
