from app.services.storage import (
    MAX_PRESIGNED_EXPIRY_SECONDS,
    StorageService,
    build_storage_key,
    get_content_type,
    validate_presigned_expiry,
)


class TestBuildStorageKey:
    def test_build_storage_key(self):
        result = build_storage_key(42, "tts", "audio.mp3")
        assert result == "projects/42/tts/audio.mp3"

    def test_build_storage_key_with_subdirectory(self):
        result = build_storage_key(7, "video", "segments/clip_001.mp4")
        assert result == "projects/7/video/segments/clip_001.mp4"


class TestGetContentType:
    def test_get_content_type_mp4(self):
        assert get_content_type("video.mp4") == "video/mp4"

    def test_get_content_type_mp3(self):
        assert get_content_type("audio.mp3") == "audio/mpeg"

    def test_get_content_type_png(self):
        assert get_content_type("thumb.png") == "image/png"

    def test_get_content_type_unknown(self):
        assert get_content_type("data.xyz") == "application/octet-stream"

    def test_get_content_type_case_insensitive(self):
        assert get_content_type("VIDEO.MP4") == "video/mp4"
        assert get_content_type("IMAGE.PNG") == "image/png"
        assert get_content_type("photo.JPG") == "image/jpeg"


class TestValidatePresignedExpiry:
    def test_validate_presigned_expiry_normal(self):
        assert validate_presigned_expiry(3600) == 3600

    def test_validate_presigned_expiry_too_large(self):
        assert validate_presigned_expiry(100_000) == MAX_PRESIGNED_EXPIRY_SECONDS

    def test_validate_presigned_expiry_negative(self):
        assert validate_presigned_expiry(-5) == 1


class TestStorageServiceInit:
    def test_storage_service_init(self):
        service = StorageService(
            endpoint="https://example.r2.cloudflarestorage.com",
            access_key="test-key",
            secret_key="test-secret",
            bucket="test-bucket",
        )
        assert service._endpoint == "https://example.r2.cloudflarestorage.com"
        assert service._bucket == "test-bucket"
        assert service._client is None
