"""ComfyUI workflow templates for SDXL + IP-Adapter image generation.

Builds JSON node graphs that ComfyUI's /prompt API accepts.
Two workflows:
  - txt2img: Text-only generation (first scene, sets style reference)
  - ipadapter: IP-Adapter generation (subsequent scenes, maintains style consistency)
"""

SDXL_CHECKPOINT = "sd_xl_base_1.0.safetensors"
IPADAPTER_MODEL = "ip-adapter-plus_sdxl_vit-h.safetensors"
CLIP_VISION_MODEL = "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"

NEGATIVE_PROMPT = (
    "blurry, low quality, distorted, deformed, ugly, bad anatomy, "
    "watermark, text, logo, signature, cropped"
)


def build_txt2img_workflow(
    prompt: str,
    width: int,
    height: int,
    seed: int = 0,
    steps: int = 25,
    cfg: float = 7.0,
    checkpoint: str = SDXL_CHECKPOINT,
) -> dict:
    """Build a ComfyUI workflow graph for text-to-image generation.

    Used for the first scene where no style reference exists yet.
    Node graph: CheckpointLoader → CLIPTextEncode → KSampler → VAEDecode → SaveImage
    """
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint},
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
                "text": NEGATIVE_PROMPT,
                "clip": ["1", 1],
            },
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1,
            },
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "normal",
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
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": "autotube",
            },
        },
    }


def build_ipadapter_workflow(
    prompt: str,
    reference_image_filename: str,
    width: int,
    height: int,
    seed: int = 0,
    steps: int = 25,
    cfg: float = 7.0,
    ipadapter_weight: float = 0.6,
    checkpoint: str = SDXL_CHECKPOINT,
    ipadapter_model: str = IPADAPTER_MODEL,
    clip_vision_model: str = CLIP_VISION_MODEL,
) -> dict:
    """Build a ComfyUI workflow graph with IP-Adapter for style consistency.

    Loads a reference image (first scene's output) and uses IP-Adapter to
    maintain visual style across subsequent scenes.

    Node graph: txt2img base + IPAdapterModelLoader + CLIPVisionLoader
                + LoadImage(reference) + IPAdapterApply → KSampler → SaveImage
    """
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint},
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
                "text": NEGATIVE_PROMPT,
                "clip": ["1", 1],
            },
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1,
            },
        },
        # IP-Adapter nodes
        "10": {
            "class_type": "IPAdapterModelLoader",
            "inputs": {"ipadapter_file": ipadapter_model},
        },
        "11": {
            "class_type": "CLIPVisionLoader",
            "inputs": {"clip_name": clip_vision_model},
        },
        "12": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_image_filename},
        },
        "13": {
            "class_type": "IPAdapterApply",
            "inputs": {
                "ipadapter": ["10", 0],
                "clip_vision": ["11", 0],
                "image": ["12", 0],
                "model": ["1", 0],
                "weight": ipadapter_weight,
                "noise": 0.0,
                "weight_type": "linear",
                "start_at": 0.0,
                "end_at": 1.0,
            },
        },
        # KSampler uses IP-Adapter-applied model
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["13", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "normal",
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
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": "autotube",
            },
        },
    }
