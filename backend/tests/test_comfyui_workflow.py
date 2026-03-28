from app.workers.comfyui_workflow import (
    build_txt2img_workflow,
    build_ipadapter_workflow,
    SDXL_CHECKPOINT,
    IPADAPTER_MODEL,
    CLIP_VISION_MODEL,
    NEGATIVE_PROMPT,
)


def test_build_txt2img_workflow_structure():
    workflow = build_txt2img_workflow("a cat", 1024, 1024, seed=42)

    node_types = {v["class_type"] for v in workflow.values()}
    assert "CheckpointLoaderSimple" in node_types
    assert "CLIPTextEncode" in node_types
    assert "KSampler" in node_types
    assert "VAEDecode" in node_types
    assert "SaveImage" in node_types
    assert "EmptyLatentImage" in node_types


def test_build_txt2img_workflow_prompt_and_seed():
    workflow = build_txt2img_workflow("sunset over ocean", 512, 768, seed=99)

    # Positive prompt node should contain the text
    positive_node = workflow["2"]
    assert positive_node["inputs"]["text"] == "sunset over ocean"

    # Negative prompt should be the default
    negative_node = workflow["3"]
    assert negative_node["inputs"]["text"] == NEGATIVE_PROMPT

    # KSampler should have seed and dimensions
    ksampler = workflow["5"]
    assert ksampler["inputs"]["seed"] == 99

    # EmptyLatentImage dimensions
    latent = workflow["4"]
    assert latent["inputs"]["width"] == 512
    assert latent["inputs"]["height"] == 768


def test_build_txt2img_workflow_checkpoint():
    workflow = build_txt2img_workflow("test", 512, 512)
    loader = workflow["1"]
    assert loader["inputs"]["ckpt_name"] == SDXL_CHECKPOINT

    custom_workflow = build_txt2img_workflow(
        "test", 512, 512, checkpoint="custom_model.safetensors"
    )
    assert custom_workflow["1"]["inputs"]["ckpt_name"] == "custom_model.safetensors"


def test_build_ipadapter_workflow_has_reference():
    workflow = build_ipadapter_workflow(
        "a dog in same style",
        reference_image_filename="ref_scene_0.png",
        width=1024,
        height=1792,
        seed=1,
    )

    node_types = {v["class_type"] for v in workflow.values()}
    assert "IPAdapterModelLoader" in node_types
    assert "CLIPVisionLoader" in node_types
    assert "LoadImage" in node_types
    assert "IPAdapterApply" in node_types

    # Find LoadImage node and check reference filename
    load_image_nodes = [
        v for v in workflow.values() if v["class_type"] == "LoadImage"
    ]
    assert len(load_image_nodes) == 1
    assert load_image_nodes[0]["inputs"]["image"] == "ref_scene_0.png"


def test_build_ipadapter_workflow_dimensions():
    workflow = build_ipadapter_workflow(
        "test prompt",
        reference_image_filename="ref.png",
        width=1792,
        height=1024,
    )

    latent = workflow["4"]
    assert latent["inputs"]["width"] == 1792
    assert latent["inputs"]["height"] == 1024


def test_build_ipadapter_workflow_model_names():
    workflow = build_ipadapter_workflow(
        "test", "ref.png", 512, 512,
    )

    ipadapter_loader = workflow["10"]
    assert ipadapter_loader["inputs"]["ipadapter_file"] == IPADAPTER_MODEL

    clip_vision_loader = workflow["11"]
    assert clip_vision_loader["inputs"]["clip_name"] == CLIP_VISION_MODEL


def test_build_ipadapter_workflow_weight():
    workflow = build_ipadapter_workflow(
        "test", "ref.png", 512, 512, ipadapter_weight=0.8,
    )

    apply_node = workflow["13"]
    assert apply_node["inputs"]["weight"] == 0.8


def test_build_ipadapter_ksampler_uses_ipadapter_model():
    """KSampler should reference the IP-Adapter applied model, not the raw checkpoint."""
    workflow = build_ipadapter_workflow("test", "ref.png", 512, 512)

    ksampler = workflow["5"]
    # model input should reference node 13 (IPAdapterApply), not node 1 (checkpoint)
    assert ksampler["inputs"]["model"] == ["13", 0]
