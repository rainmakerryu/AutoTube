from unittest.mock import patch, MagicMock

import pytest

from app.workers.comfyui_client import (
    check_comfyui_health,
    submit_workflow,
    poll_comfyui_result,
    download_comfyui_image,
    upload_reference_image,
    ComfyUIError,
    COMFYUI_DEFAULT_URL,
)


class TestCheckHealth:
    def test_health_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("app.workers.comfyui_client.httpx.get", return_value=mock_response):
            assert check_comfyui_health(COMFYUI_DEFAULT_URL) is True

    def test_health_unreachable(self):
        import httpx

        with patch(
            "app.workers.comfyui_client.httpx.get",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            assert check_comfyui_health(COMFYUI_DEFAULT_URL) is False

    def test_health_server_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("app.workers.comfyui_client.httpx.get", return_value=mock_response):
            assert check_comfyui_health(COMFYUI_DEFAULT_URL) is False


class TestSubmitWorkflow:
    def test_submit_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"prompt_id": "abc-123"}
        mock_response.raise_for_status = MagicMock()

        with patch("app.workers.comfyui_client.httpx.post", return_value=mock_response):
            result = submit_workflow(COMFYUI_DEFAULT_URL, {"1": {}})
            assert result == "abc-123"

    def test_submit_no_prompt_id(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        with patch("app.workers.comfyui_client.httpx.post", return_value=mock_response):
            with pytest.raises(ComfyUIError, match="prompt_id"):
                submit_workflow(COMFYUI_DEFAULT_URL, {"1": {}})

    def test_submit_connection_error(self):
        import httpx

        with patch(
            "app.workers.comfyui_client.httpx.post",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            with pytest.raises(ComfyUIError, match="연결 실패"):
                submit_workflow(COMFYUI_DEFAULT_URL, {"1": {}})


class TestPollResult:
    def test_poll_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "abc-123": {
                "outputs": {
                    "7": {"images": [{"filename": "out.png", "type": "output"}]}
                }
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.workers.comfyui_client.httpx.get", return_value=mock_response):
            result = poll_comfyui_result(COMFYUI_DEFAULT_URL, "abc-123", timeout=5.0)
            assert "7" in result
            assert result["7"]["images"][0]["filename"] == "out.png"

    def test_poll_timeout(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        with patch("app.workers.comfyui_client.httpx.get", return_value=mock_response):
            with patch("app.workers.comfyui_client.time.sleep"):
                with pytest.raises(ComfyUIError, match="타임아웃"):
                    poll_comfyui_result(COMFYUI_DEFAULT_URL, "abc-123", timeout=0.01)

    def test_poll_execution_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "abc-123": {
                "status": {
                    "status_str": "error",
                    "messages": [["execution_error", {"node_id": "5"}]],
                },
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.workers.comfyui_client.httpx.get", return_value=mock_response):
            with pytest.raises(ComfyUIError, match="실행 오류"):
                poll_comfyui_result(COMFYUI_DEFAULT_URL, "abc-123", timeout=5.0)


class TestDownloadImage:
    def test_download_success(self):
        mock_response = MagicMock()
        mock_response.content = b"\x89PNG\r\n\x1a\n"
        mock_response.raise_for_status = MagicMock()

        with patch("app.workers.comfyui_client.httpx.get", return_value=mock_response):
            data = download_comfyui_image(COMFYUI_DEFAULT_URL, "test.png")
            assert data == b"\x89PNG\r\n\x1a\n"

    def test_download_failure(self):
        import httpx

        with patch(
            "app.workers.comfyui_client.httpx.get",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            with pytest.raises(ComfyUIError, match="다운로드 실패"):
                download_comfyui_image(COMFYUI_DEFAULT_URL, "test.png")


class TestUploadReferenceImage:
    def test_upload_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "ref_scene_0.png", "subfolder": ""}
        mock_response.raise_for_status = MagicMock()

        with patch("app.workers.comfyui_client.httpx.post", return_value=mock_response):
            name = upload_reference_image(
                COMFYUI_DEFAULT_URL, b"\x89PNG", "ref_scene_0.png"
            )
            assert name == "ref_scene_0.png"

    def test_upload_no_name(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        with patch("app.workers.comfyui_client.httpx.post", return_value=mock_response):
            with pytest.raises(ComfyUIError, match="파일명이 없습니다"):
                upload_reference_image(
                    COMFYUI_DEFAULT_URL, b"\x89PNG", "ref.png"
                )
