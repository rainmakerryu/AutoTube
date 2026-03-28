import pytest

from app.workers.images import (
    build_consistent_prompts,
    build_image_generation_request,
    extract_visual_keywords,
    parse_image_response,
    _parse_comfyui_dimensions,
    _extract_output_filename,
    CONSISTENCY_PROMPT_PREFIX,
    SHORTS_IMAGE_SIZE,
    LONGFORM_IMAGE_SIZE,
)


def test_extract_visual_keywords():
    scene = {
        "visual": "[장면 1]: 커피콩이 빨갛게 익어가는 모습",
        "narration": "커피는 원래 에티오피아의 염소가 발견했다고 합니다.",
    }
    result = extract_visual_keywords(scene)
    assert "커피콩이 빨갛게 익어가는 모습" in result
    assert "에티오피아" in result


def test_extract_visual_keywords_empty_narration():
    scene = {
        "visual": "[장면 1]: 아름다운 바다 풍경",
        "narration": "",
    }
    result = extract_visual_keywords(scene)
    assert "아름다운 바다 풍경" in result
    assert result.strip() == result


def test_build_image_request_gemini():
    req = build_image_generation_request(
        prompt="coffee beans ripening",
        provider="gemini",
        api_key="gemini-test-key",
        video_type="shorts",
    )
    assert "generativelanguage.googleapis.com" in req["url"]
    assert "gemini-test-key" in req["url"]
    assert req["method"] == "POST"
    assert "coffee beans ripening" in str(req["json"])


def test_build_image_request_openai():
    req = build_image_generation_request(
        prompt="coffee beans ripening",
        provider="openai",
        api_key="sk-test-key",
        video_type="shorts",
    )
    assert req["url"] == "https://api.openai.com/v1/images/generations"
    assert "Bearer sk-test-key" in req["headers"]["Authorization"]
    assert req["json"]["model"] == "dall-e-3"
    assert req["json"]["prompt"] == "coffee beans ripening"
    assert req["json"]["size"] == SHORTS_IMAGE_SIZE
    assert req["method"] == "POST"


def test_build_image_request_pexels():
    req = build_image_generation_request(
        prompt="coffee beans",
        provider="pexels",
        api_key="pexels-test-key",
        video_type="shorts",
    )
    assert "api.pexels.com" in req["url"]
    assert req["headers"]["Authorization"] == "pexels-test-key"
    assert req["params"]["query"] == "coffee beans"
    assert req["method"] == "GET"


def test_build_image_request_invalid_provider():
    with pytest.raises(ValueError, match="지원하지 않는"):
        build_image_generation_request(
            prompt="test",
            provider="invalid",
            api_key="key",
        )


def test_build_image_request_longform_size():
    req = build_image_generation_request(
        prompt="coffee beans",
        provider="openai",
        api_key="sk-test-key",
        video_type="longform",
    )
    assert req["json"]["size"] == LONGFORM_IMAGE_SIZE


def test_parse_image_response_openai():
    response_json = {
        "data": [
            {"url": "https://oaidalleapiprodscus.blob.core.windows.net/image.png"}
        ]
    }
    result = parse_image_response("openai", response_json)
    assert result == "https://oaidalleapiprodscus.blob.core.windows.net/image.png"


def test_parse_image_response_pexels():
    response_json = {
        "photos": [
            {
                "src": {
                    "large": "https://images.pexels.com/photos/12345/pexels-photo-12345.jpeg",
                    "original": "https://images.pexels.com/photos/12345/original.jpeg",
                }
            }
        ]
    }
    result = parse_image_response("pexels", response_json)
    assert result == "https://images.pexels.com/photos/12345/pexels-photo-12345.jpeg"


def test_parse_image_response_pexels_empty():
    response_json = {"photos": []}
    result = parse_image_response("pexels", response_json)
    assert result is None


def test_build_consistent_prompts_single_scene():
    scenes = [{"visual": "[장면 1]: 파란 하늘", "narration": "맑은 날씨입니다."}]
    prompts = build_consistent_prompts(scenes)
    assert len(prompts) == 1
    assert CONSISTENCY_PROMPT_PREFIX in prompts[0]
    assert "Style reference:" in prompts[0]


def test_build_consistent_prompts_multiple_scenes():
    scenes = [
        {"visual": "[장면 1]: 커피콩 클로즈업", "narration": "에티오피아산 원두입니다."},
        {"visual": "[장면 2]: 바리스타 작업", "narration": "에스프레소를 추출합니다."},
        {"visual": "[장면 3]: 완성된 커피", "narration": "향기로운 커피입니다."},
    ]
    prompts = build_consistent_prompts(scenes)
    assert len(prompts) == 3
    # 첫 번째 장면: 스타일 기준 설정
    assert "Style reference:" in prompts[0]
    # 두 번째, 세 번째 장면: 스타일 참조 포함
    assert "Match the established style:" in prompts[1]
    assert "Match the established style:" in prompts[2]
    assert "Scene:" in prompts[1]
    assert "Scene:" in prompts[2]


def test_build_consistent_prompts_empty():
    prompts = build_consistent_prompts([])
    assert prompts == []


def test_build_consistent_prompts_prefix_consistency():
    scenes = [
        {"visual": "Scene 1: nature", "narration": ""},
        {"visual": "Scene 2: city", "narration": ""},
    ]
    prompts = build_consistent_prompts(scenes)
    for prompt in prompts:
        assert prompt.startswith(CONSISTENCY_PROMPT_PREFIX)


def test_build_image_request_comfyui():
    req = build_image_generation_request(
        prompt="coffee beans ripening",
        provider="comfyui",
        api_key="http://127.0.0.1:8188",
        video_type="shorts",
    )
    assert req["method"] == "COMFYUI"


def test_parse_comfyui_dimensions_shorts():
    w, h = _parse_comfyui_dimensions("shorts")
    assert w == 1024
    assert h == 1792


def test_parse_comfyui_dimensions_longform():
    w, h = _parse_comfyui_dimensions("longform")
    assert w == 1792
    assert h == 1024


def test_extract_output_filename_found():
    outputs = {
        "7": {
            "images": [
                {"filename": "autotube_00001_.png", "subfolder": "", "type": "output"}
            ]
        }
    }
    assert _extract_output_filename(outputs) == "autotube_00001_.png"


def test_extract_output_filename_empty():
    outputs = {"7": {"images": []}}
    assert _extract_output_filename(outputs) is None


def test_extract_output_filename_no_images_key():
    outputs = {"7": {"text": "hello"}}
    assert _extract_output_filename(outputs) is None
