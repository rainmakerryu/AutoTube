"""ComfyUI workflow templates for video generation (img2vid + txt2vid).

Builds JSON node graphs that ComfyUI's /prompt API accepts.
Six workflows:
  - animatediff: SD1.5 + AnimateDiff img2vid
  - svd: Stable Video Diffusion XT img2vid
  - wan21_img2vid: Wan2.1 image-to-video
  - wan21_txt2vid: Wan2.1 text-to-video
  - cogvideox_img2vid: CogVideoX image-to-video
  - cogvideox_txt2vid: CogVideoX text-to-video

All workflows output MP4 via VHS_VideoCombine (VideoHelperSuite).
"""
from __future__ import annotations

# --- Model checkpoints ---
ANIMATEDIFF_CHECKPOINT = "v1-5-pruned-emaonly.safetensors"
ANIMATEDIFF_MOTION_MODULE = "mm_sd15_v3.safetensors"
SVD_CHECKPOINT = "svd_xt.safetensors"
WAN21_I2V_MODEL = "wan2.1_i2v_720p.safetensors"
WAN21_T2V_MODEL = "wan2.1_t2v_720p.safetensors"
COGVIDEOX_MODEL = "CogVideoX-5B"

VHS_FORMAT = "video/h264-mp4"
VIDEO_FILENAME_PREFIX = "autotube_video"

NEGATIVE_PROMPT_VIDEO = (
    "blurry, low quality, distorted, deformed, watermark, text, "
    "static image, no motion, flickering, artifacts"
)

# --- Default generation parameters per model ---
DEFAULT_VIDEO_PARAMS: dict[str, dict] = {
    "animatediff": {"frames": 16, "fps": 8},
    "svd": {"frames": 25, "fps": 6, "motion_bucket_id": 127, "augmentation_level": 0.0},
    "wan21": {"frames": 81, "fps": 16},
    "cogvideox": {"frames": 49, "fps": 8},
}

# --- Default resolutions per model (width, height for landscape) ---
_MODEL_RESOLUTIONS: dict[str, tuple[int, int]] = {
    "animatediff": (512, 512),
    "svd": (1024, 576),
    "wan21": (832, 480),
    "cogvideox": (720, 480),
}


def get_video_resolution(video_type: str, model: str) -> tuple[int, int]:
    """Return (width, height) based on video type and model defaults.

    For 'shorts' (portrait): swap width and height.
    For 'long' (landscape): use default model dimensions.
    """
    w, h = _MODEL_RESOLUTIONS.get(model, (512, 512))
    if video_type == "shorts":
        return (h, w)
    return (w, h)


def _vhs_video_combine_node(source_node: str, fps: int) -> dict:
    """Build a VHS_VideoCombine node dict."""
    return {
        "class_type": "VHS_VideoCombine",
        "inputs": {
            "images": [source_node, 0],
            "frame_rate": fps,
            "loop_count": 0,
            "filename_prefix": VIDEO_FILENAME_PREFIX,
            "format": VHS_FORMAT,
            "save_output": True,
        },
    }


# ============================================================
# 1. AnimateDiff (img2vid) — SD1.5 + motion module
# ============================================================

def build_animatediff_workflow(
    image_filename: str,
    prompt: str,
    negative_prompt: str = NEGATIVE_PROMPT_VIDEO,
    width: int = 512,
    height: int = 512,
    frames: int = 16,
    fps: int = 8,
    seed: int = 0,
    steps: int = 20,
    cfg: float = 7.0,
    denoise: float = 0.75,
) -> dict:
    """AnimateDiff img2vid: Load image → encode to latent → animate with motion module.

    Node graph:
      CheckpointLoader → ADE_AnimateDiffLoaderWithContext →
      LoadImage → VAEEncode → KSampler → VAEDecode → VHS_VideoCombine
    """
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": ANIMATEDIFF_CHECKPOINT},
        },
        "2": {
            "class_type": "ADE_AnimateDiffLoaderWithContext",
            "inputs": {
                "model": ["1", 0],
                "model_name": ANIMATEDIFF_MOTION_MODULE,
                "beta_schedule": "sqrt_linear (AnimateDiff)",
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["1", 1],
            },
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative_prompt,
                "clip": ["1", 1],
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": image_filename},
        },
        "6": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["5", 0],
                "vae": ["1", 2],
            },
        },
        "7": {
            "class_type": "RepeatLatentBatch",
            "inputs": {
                "samples": ["6", 0],
                "amount": frames,
            },
        },
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["7", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": denoise,
            },
        },
        "9": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["8", 0],
                "vae": ["1", 2],
            },
        },
        "10": _vhs_video_combine_node("9", fps),
    }


# ============================================================
# 2. SVD XT (img2vid) — image-conditioned, no text prompt
# ============================================================

def build_svd_workflow(
    image_filename: str,
    width: int = 1024,
    height: int = 576,
    frames: int = 25,
    fps: int = 6,
    motion_bucket_id: int = 127,
    augmentation_level: float = 0.0,
    seed: int = 0,
    steps: int = 20,
    cfg: float = 2.5,
) -> dict:
    """SVD XT img2vid: image-conditioned video generation (no text prompt).

    Node graph:
      ImageOnlyCheckpointLoader → LoadImage → SVD_img2vid_Conditioning →
      VideoLinearCFGGuidance → KSampler → VAEDecode → VHS_VideoCombine
    """
    return {
        "1": {
            "class_type": "ImageOnlyCheckpointLoader",
            "inputs": {"ckpt_name": SVD_CHECKPOINT},
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": image_filename},
        },
        "3": {
            "class_type": "SVD_img2vid_Conditioning",
            "inputs": {
                "clip_vision": ["1", 1],
                "init_image": ["2", 0],
                "vae": ["1", 2],
                "width": width,
                "height": height,
                "video_frames": frames,
                "motion_bucket_id": motion_bucket_id,
                "fps": fps,
                "augmentation_level": augmentation_level,
            },
        },
        "4": {
            "class_type": "VideoLinearCFGGuidance",
            "inputs": {
                "model": ["1", 0],
                "min_cfg": 1.0,
            },
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["4", 0],
                "positive": ["3", 0],
                "negative": ["3", 1],
                "latent_image": ["3", 2],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "karras",
                "denoise": 1.0,
            },
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2],
            },
        },
        "7": _vhs_video_combine_node("6", fps),
    }


# ============================================================
# 3. Wan2.1 img2vid
# ============================================================

def build_wan21_img2vid_workflow(
    image_filename: str,
    prompt: str,
    negative_prompt: str = NEGATIVE_PROMPT_VIDEO,
    width: int = 832,
    height: int = 480,
    frames: int = 81,
    fps: int = 16,
    seed: int = 0,
    steps: int = 30,
    cfg: float = 5.0,
) -> dict:
    """Wan2.1 img2vid: image + text conditioned video generation.

    Node graph:
      DownloadAndLoadWan2_1Model → CLIPTextEncode →
      LoadImage → WanImageToVideo → VHS_VideoCombine
    """
    return {
        "1": {
            "class_type": "DownloadAndLoadWan2_1Model",
            "inputs": {
                "model": WAN21_I2V_MODEL,
                "base_precision": "bf16",
                "quantization": "disabled",
            },
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["1", 1],
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative_prompt,
                "clip": ["1", 1],
            },
        },
        "4": {
            "class_type": "LoadImage",
            "inputs": {"image": image_filename},
        },
        "5": {
            "class_type": "WanImageToVideo",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "image": ["4", 0],
                "width": width,
                "height": height,
                "num_frames": frames,
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
            },
        },
        "6": _vhs_video_combine_node("5", fps),
    }


# ============================================================
# 4. Wan2.1 txt2vid
# ============================================================

def build_wan21_txt2vid_workflow(
    prompt: str,
    negative_prompt: str = NEGATIVE_PROMPT_VIDEO,
    width: int = 832,
    height: int = 480,
    frames: int = 81,
    fps: int = 16,
    seed: int = 0,
    steps: int = 30,
    cfg: float = 5.0,
) -> dict:
    """Wan2.1 txt2vid: text-only video generation.

    Node graph:
      DownloadAndLoadWan2_1Model → CLIPTextEncode →
      WanTextToVideo → VHS_VideoCombine
    """
    return {
        "1": {
            "class_type": "DownloadAndLoadWan2_1Model",
            "inputs": {
                "model": WAN21_T2V_MODEL,
                "base_precision": "bf16",
                "quantization": "disabled",
            },
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["1", 1],
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative_prompt,
                "clip": ["1", 1],
            },
        },
        "4": {
            "class_type": "WanTextToVideo",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "width": width,
                "height": height,
                "num_frames": frames,
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
            },
        },
        "5": _vhs_video_combine_node("4", fps),
    }


# ============================================================
# 5. CogVideoX img2vid
# ============================================================

def build_cogvideox_img2vid_workflow(
    image_filename: str,
    prompt: str,
    negative_prompt: str = NEGATIVE_PROMPT_VIDEO,
    width: int = 720,
    height: int = 480,
    frames: int = 49,
    fps: int = 8,
    seed: int = 0,
    steps: int = 50,
    cfg: float = 6.0,
) -> dict:
    """CogVideoX img2vid: image + text conditioned video generation.

    Node graph:
      CogVideoXLoader → CogVideoXTextEncode → LoadImage →
      CogVideoXImageToVideo → CogVideoXDecode → VHS_VideoCombine
    """
    return {
        "1": {
            "class_type": "CogVideoXLoader",
            "inputs": {"model_name": COGVIDEOX_MODEL},
        },
        "2": {
            "class_type": "CogVideoXTextEncode",
            "inputs": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "pipeline": ["1", 0],
            },
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {"image": image_filename},
        },
        "4": {
            "class_type": "CogVideoXImageToVideo",
            "inputs": {
                "pipeline": ["1", 0],
                "embeds": ["2", 0],
                "image": ["3", 0],
                "width": width,
                "height": height,
                "num_frames": frames,
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
            },
        },
        "5": {
            "class_type": "CogVideoXDecode",
            "inputs": {
                "pipeline": ["1", 0],
                "samples": ["4", 0],
            },
        },
        "6": _vhs_video_combine_node("5", fps),
    }


# ============================================================
# 6. CogVideoX txt2vid
# ============================================================

def build_cogvideox_txt2vid_workflow(
    prompt: str,
    negative_prompt: str = NEGATIVE_PROMPT_VIDEO,
    width: int = 720,
    height: int = 480,
    frames: int = 49,
    fps: int = 8,
    seed: int = 0,
    steps: int = 50,
    cfg: float = 6.0,
) -> dict:
    """CogVideoX txt2vid: text-only video generation.

    Node graph:
      CogVideoXLoader → CogVideoXTextEncode →
      CogVideoXTextToVideo → CogVideoXDecode → VHS_VideoCombine
    """
    return {
        "1": {
            "class_type": "CogVideoXLoader",
            "inputs": {"model_name": COGVIDEOX_MODEL},
        },
        "2": {
            "class_type": "CogVideoXTextEncode",
            "inputs": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "pipeline": ["1", 0],
            },
        },
        "3": {
            "class_type": "CogVideoXTextToVideo",
            "inputs": {
                "pipeline": ["1", 0],
                "embeds": ["2", 0],
                "width": width,
                "height": height,
                "num_frames": frames,
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
            },
        },
        "4": {
            "class_type": "CogVideoXDecode",
            "inputs": {
                "pipeline": ["1", 0],
                "samples": ["3", 0],
            },
        },
        "5": _vhs_video_combine_node("4", fps),
    }
