"""Tests for ComfyUI video workflow builders."""
from __future__ import annotations

from app.workers.comfyui_video_workflow import (
    build_animatediff_workflow,
    build_svd_workflow,
    build_wan21_img2vid_workflow,
    build_wan21_txt2vid_workflow,
    build_cogvideox_img2vid_workflow,
    build_cogvideox_txt2vid_workflow,
    get_video_resolution,
    DEFAULT_VIDEO_PARAMS,
    VHS_FORMAT,
    VIDEO_FILENAME_PREFIX,
    ANIMATEDIFF_CHECKPOINT,
    SVD_CHECKPOINT,
    WAN21_I2V_MODEL,
    WAN21_T2V_MODEL,
    COGVIDEOX_MODEL,
)


# --- Helper to find VHS_VideoCombine node ---

def _find_vhs_node(workflow: dict) -> dict | None:
    for node in workflow.values():
        if node.get("class_type") == "VHS_VideoCombine":
            return node
    return None


def _has_node_type(workflow: dict, class_type: str) -> bool:
    return any(n.get("class_type") == class_type for n in workflow.values())


# --- VHS_VideoCombine in every workflow ---

ALL_IMG2VID_BUILDERS = [
    ("animatediff", lambda: build_animatediff_workflow("test.png", "a cat")),
    ("svd", lambda: build_svd_workflow("test.png")),
    ("wan21_i2v", lambda: build_wan21_img2vid_workflow("test.png", "a cat")),
    ("cogvideox_i2v", lambda: build_cogvideox_img2vid_workflow("test.png", "a cat")),
]

ALL_TXT2VID_BUILDERS = [
    ("wan21_t2v", lambda: build_wan21_txt2vid_workflow("a cat")),
    ("cogvideox_t2v", lambda: build_cogvideox_txt2vid_workflow("a cat")),
]

ALL_BUILDERS = ALL_IMG2VID_BUILDERS + ALL_TXT2VID_BUILDERS


def test_all_workflows_have_vhs_node():
    for name, builder in ALL_BUILDERS:
        wf = builder()
        vhs = _find_vhs_node(wf)
        assert vhs is not None, f"{name} workflow missing VHS_VideoCombine"
        assert vhs["inputs"]["format"] == VHS_FORMAT
        assert vhs["inputs"]["filename_prefix"] == VIDEO_FILENAME_PREFIX


def test_all_workflows_return_dict():
    for name, builder in ALL_BUILDERS:
        wf = builder()
        assert isinstance(wf, dict), f"{name} did not return dict"
        assert len(wf) > 0, f"{name} returned empty dict"


def test_img2vid_builders_have_load_image():
    for name, builder in ALL_IMG2VID_BUILDERS:
        wf = builder()
        assert _has_node_type(wf, "LoadImage"), f"{name} missing LoadImage node"


def test_txt2vid_builders_have_no_load_image():
    for name, builder in ALL_TXT2VID_BUILDERS:
        wf = builder()
        assert not _has_node_type(wf, "LoadImage"), f"{name} should not have LoadImage"


# --- AnimateDiff ---

def test_animatediff_nodes():
    wf = build_animatediff_workflow("scene1.png", "a running dog", seed=42, frames=24)
    assert _has_node_type(wf, "CheckpointLoaderSimple")
    assert _has_node_type(wf, "ADE_AnimateDiffLoaderWithContext")
    assert _has_node_type(wf, "KSampler")
    assert _has_node_type(wf, "RepeatLatentBatch")
    assert wf["1"]["inputs"]["ckpt_name"] == ANIMATEDIFF_CHECKPOINT
    assert wf["8"]["inputs"]["seed"] == 42
    assert wf["7"]["inputs"]["amount"] == 24


def test_animatediff_prompt_encoding():
    wf = build_animatediff_workflow("img.png", "positive prompt", negative_prompt="bad stuff")
    assert wf["3"]["inputs"]["text"] == "positive prompt"
    assert wf["4"]["inputs"]["text"] == "bad stuff"


# --- SVD ---

def test_svd_nodes():
    wf = build_svd_workflow("scene.png", frames=30, motion_bucket_id=200, seed=7)
    assert _has_node_type(wf, "ImageOnlyCheckpointLoader")
    assert _has_node_type(wf, "SVD_img2vid_Conditioning")
    assert _has_node_type(wf, "VideoLinearCFGGuidance")
    assert wf["1"]["inputs"]["ckpt_name"] == SVD_CHECKPOINT
    assert wf["3"]["inputs"]["video_frames"] == 30
    assert wf["3"]["inputs"]["motion_bucket_id"] == 200
    assert wf["5"]["inputs"]["seed"] == 7


def test_svd_no_text_prompt():
    wf = build_svd_workflow("scene.png")
    assert not _has_node_type(wf, "CLIPTextEncode")


# --- Wan2.1 img2vid ---

def test_wan21_img2vid_nodes():
    wf = build_wan21_img2vid_workflow("img.png", "ocean waves", frames=60, seed=99)
    assert _has_node_type(wf, "DownloadAndLoadWan2_1Model")
    assert _has_node_type(wf, "WanImageToVideo")
    assert wf["1"]["inputs"]["model"] == WAN21_I2V_MODEL
    assert wf["5"]["inputs"]["num_frames"] == 60
    assert wf["5"]["inputs"]["seed"] == 99


def test_wan21_img2vid_prompt():
    wf = build_wan21_img2vid_workflow("img.png", "sunset", negative_prompt="ugly")
    assert wf["2"]["inputs"]["text"] == "sunset"
    assert wf["3"]["inputs"]["text"] == "ugly"


# --- Wan2.1 txt2vid ---

def test_wan21_txt2vid_nodes():
    wf = build_wan21_txt2vid_workflow("a beautiful sunset", frames=40, seed=5)
    assert _has_node_type(wf, "DownloadAndLoadWan2_1Model")
    assert _has_node_type(wf, "WanTextToVideo")
    assert not _has_node_type(wf, "WanImageToVideo")
    assert wf["1"]["inputs"]["model"] == WAN21_T2V_MODEL
    assert wf["4"]["inputs"]["num_frames"] == 40
    assert wf["4"]["inputs"]["seed"] == 5


# --- CogVideoX img2vid ---

def test_cogvideox_img2vid_nodes():
    wf = build_cogvideox_img2vid_workflow("img.png", "city lights", frames=25, seed=11)
    assert _has_node_type(wf, "CogVideoXLoader")
    assert _has_node_type(wf, "CogVideoXTextEncode")
    assert _has_node_type(wf, "CogVideoXImageToVideo")
    assert _has_node_type(wf, "CogVideoXDecode")
    assert wf["1"]["inputs"]["model_name"] == COGVIDEOX_MODEL
    assert wf["4"]["inputs"]["num_frames"] == 25
    assert wf["4"]["inputs"]["seed"] == 11


# --- CogVideoX txt2vid ---

def test_cogvideox_txt2vid_nodes():
    wf = build_cogvideox_txt2vid_workflow("a forest", frames=30, seed=22)
    assert _has_node_type(wf, "CogVideoXLoader")
    assert _has_node_type(wf, "CogVideoXTextEncode")
    assert _has_node_type(wf, "CogVideoXTextToVideo")
    assert _has_node_type(wf, "CogVideoXDecode")
    assert not _has_node_type(wf, "CogVideoXImageToVideo")
    assert wf["3"]["inputs"]["num_frames"] == 30
    assert wf["3"]["inputs"]["seed"] == 22


# --- get_video_resolution ---

def test_video_resolution_long():
    w, h = get_video_resolution("long", "svd")
    assert w == 1024
    assert h == 576


def test_video_resolution_shorts():
    w, h = get_video_resolution("shorts", "svd")
    assert w == 576
    assert h == 1024


def test_video_resolution_animatediff_square():
    w, h = get_video_resolution("long", "animatediff")
    assert w == 512
    assert h == 512


def test_video_resolution_unknown_model():
    w, h = get_video_resolution("long", "unknown_model")
    assert w == 512
    assert h == 512


# --- DEFAULT_VIDEO_PARAMS ---

def test_default_params_all_models():
    expected_models = {"animatediff", "svd", "wan21", "cogvideox"}
    assert expected_models == set(DEFAULT_VIDEO_PARAMS.keys())


def test_default_params_have_frames_and_fps():
    for model, params in DEFAULT_VIDEO_PARAMS.items():
        assert "frames" in params, f"{model} missing 'frames'"
        assert "fps" in params, f"{model} missing 'fps'"
        assert params["frames"] > 0
        assert params["fps"] > 0


# --- VHS node FPS propagation ---

def test_vhs_fps_matches_input():
    wf = build_animatediff_workflow("test.png", "cat", fps=12)
    vhs = _find_vhs_node(wf)
    assert vhs["inputs"]["frame_rate"] == 12

    wf2 = build_svd_workflow("test.png", fps=10)
    vhs2 = _find_vhs_node(wf2)
    assert vhs2["inputs"]["frame_rate"] == 10

    wf3 = build_wan21_txt2vid_workflow("test", fps=24)
    vhs3 = _find_vhs_node(wf3)
    assert vhs3["inputs"]["frame_rate"] == 24
