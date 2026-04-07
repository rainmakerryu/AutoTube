"""오디오 후처리 워커.

TTS 출력 오디오에 음량 정규화, 압축, 대역 제한, 잔향 제거 등을 적용한다.
pydub + ffmpeg 기반.
"""
from __future__ import annotations

import os
import subprocess
import tempfile

import httpx

from app.celery_app import celery_app
from app.services.storage import (
    build_storage_key,
    save_local,
    save_to_output_dir,
)

API_TIMEOUT_SECONDS = 120.0
AUDIO_FILENAME = "audio_processed.mp3"
AUDIO_CONTENT_TYPE = "audio/mpeg"
TARGET_DBFS = -20.0  # 정규화 목표 dBFS
COMPRESSOR_THRESHOLD = -30.0
COMPRESSOR_RATIO = 4.0
LOWCUT_HZ = 80
HIGHCUT_HZ = 12000

POSTPROCESS_MODES = {
    "normalize": "음량 정규화 - 전체 음량을 일정하게 조정",
    "compress_normalize": "압축 + 정규화 - 동적 범위 압축 후 음량 정규화",
    "dynamic_normalize": "동적 정규화 - 구간별 음량을 자동 조정",
    "band_limit_normalize": "대역 제한 + 정규화 - 불필요한 저/고주파 제거 후 정규화",
    "dereverb_eq": "De-Reverb (EQ) - EQ 기반 잔향 제거",
    "dereverb_complex": "De-Reverb (복합) - 복합 필터 기반 잔향 제거",
}


def _download_audio(url: str, dest_path: str) -> str:
    """URL에서 오디오 파일을 다운로드."""
    resp = httpx.get(url, timeout=API_TIMEOUT_SECONDS)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(resp.content)
    return dest_path


def _normalize(audio):
    """pydub AudioSegment 음량 정규화."""
    change = TARGET_DBFS - audio.dBFS
    return audio.apply_gain(change)


def _compress_normalize(audio):
    """동적 범위 압축 후 정규화.

    pydub에 내장 압축기가 없으므로 간단한 소프트 리미터를 적용한다.
    """
    # 소프트 리미터: 너무 큰 구간을 줄인다
    threshold_linear = 10 ** (COMPRESSOR_THRESHOLD / 20)
    chunk_ms = 50
    chunks = [audio[i:i + chunk_ms] for i in range(0, len(audio), chunk_ms)]
    processed_chunks = []
    for chunk in chunks:
        if chunk.dBFS > COMPRESSOR_THRESHOLD:
            reduction = (chunk.dBFS - COMPRESSOR_THRESHOLD) * (1 - 1 / COMPRESSOR_RATIO)
            chunk = chunk.apply_gain(-reduction)
        processed_chunks.append(chunk)
    if not processed_chunks:
        return audio
    result = processed_chunks[0]
    for c in processed_chunks[1:]:
        result += c
    return _normalize(result)


def _dynamic_normalize(audio):
    """구간별 동적 정규화 (1초 단위)."""
    chunk_ms = 1000
    chunks = [audio[i:i + chunk_ms] for i in range(0, len(audio), chunk_ms)]
    processed = []
    for chunk in chunks:
        if chunk.dBFS != float("-inf"):
            change = TARGET_DBFS - chunk.dBFS
            # 급격한 변화 방지
            change = max(-10, min(10, change))
            chunk = chunk.apply_gain(change)
        processed.append(chunk)
    if not processed:
        return audio
    result = processed[0]
    for c in processed[1:]:
        result += c
    return result


def _ffmpeg_filter(input_path: str, output_path: str, af_filter: str) -> str:
    """ffmpeg 오디오 필터를 적용한다."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-af", af_filter,
        "-ar", "44100", "-ac", "1",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(
            f"ffmpeg 필터 적용 실패 (exit {result.returncode}): {stderr[:500]}"
        )
    return output_path


def _band_limit_normalize(input_path: str, output_path: str) -> str:
    """대역 제한 + 정규화 (ffmpeg)."""
    af = (
        f"highpass=f={LOWCUT_HZ},"
        f"lowpass=f={HIGHCUT_HZ},"
        "loudnorm=I=-20:TP=-1.5:LRA=11"
    )
    return _ffmpeg_filter(input_path, output_path, af)


def _dereverb_eq(input_path: str, output_path: str) -> str:
    """EQ 기반 잔향 제거 (ffmpeg)."""
    af = (
        "equalizer=f=200:t=q:w=2:g=-3,"
        "equalizer=f=500:t=q:w=1:g=-2,"
        "equalizer=f=2000:t=q:w=1:g=2,"
        "loudnorm=I=-20:TP=-1.5:LRA=11"
    )
    return _ffmpeg_filter(input_path, output_path, af)


def _dereverb_complex(input_path: str, output_path: str) -> str:
    """복합 필터 기반 잔향 제거 (ffmpeg)."""
    af = (
        f"highpass=f={LOWCUT_HZ},"
        f"lowpass=f={HIGHCUT_HZ},"
        "afftdn=nf=-25,"
        "equalizer=f=300:t=q:w=2:g=-3,"
        "equalizer=f=3000:t=q:w=1:g=2,"
        "loudnorm=I=-20:TP=-1.5:LRA=11"
    )
    return _ffmpeg_filter(input_path, output_path, af)


@celery_app.task(name="pipeline.audio_postprocess")
def audio_postprocess_task(
    project_id: int,
    audio_url: str,
    mode: str = "normalize",
) -> dict:
    """TTS 출력 오디오를 후처리한다."""
    if mode not in POSTPROCESS_MODES:
        raise ValueError(
            f"지원하지 않는 후처리 모드입니다: '{mode}'. "
            f"허용: {', '.join(sorted(POSTPROCESS_MODES.keys()))}"
        )

    work_dir = tempfile.mkdtemp(prefix="autotube_audiopp_")
    try:
        # 1. 오디오 다운로드
        input_path = os.path.join(work_dir, "input.mp3")
        _download_audio(audio_url, input_path)
        output_path = os.path.join(work_dir, AUDIO_FILENAME)

        original_rms = 0.0
        processed_rms = 0.0

        # 2. pydub 기반 모드 (normalize, compress_normalize, dynamic_normalize)
        if mode in ("normalize", "compress_normalize", "dynamic_normalize"):
            from pydub import AudioSegment

            audio = AudioSegment.from_file(input_path)
            original_rms = audio.dBFS

            if mode == "normalize":
                processed = _normalize(audio)
            elif mode == "compress_normalize":
                processed = _compress_normalize(audio)
            else:
                processed = _dynamic_normalize(audio)

            processed_rms = processed.dBFS
            processed.export(output_path, format="mp3")

        # 3. ffmpeg 기반 모드
        elif mode == "band_limit_normalize":
            _band_limit_normalize(input_path, output_path)
        elif mode == "dereverb_eq":
            _dereverb_eq(input_path, output_path)
        elif mode == "dereverb_complex":
            _dereverb_complex(input_path, output_path)

        # 4. 저장
        with open(output_path, "rb") as f:
            audio_data = f.read()

        key = build_storage_key(project_id, "audio_post", AUDIO_FILENAME)
        processed_url = save_local(key, audio_data)
        save_to_output_dir(project_id, AUDIO_FILENAME, audio_data)

        return {
            "audio_url": processed_url,
            "mode": mode,
            "original_rms": round(original_rms, 2),
            "processed_rms": round(processed_rms, 2),
            "provider": "local",
        }
    finally:
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)
