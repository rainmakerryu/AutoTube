DEFAULT_PRESIGNED_EXPIRY_SECONDS = 3600  # 1시간
MAX_PRESIGNED_EXPIRY_SECONDS = 86400  # 24시간
MIN_PRESIGNED_EXPIRY_SECONDS = 1

UPLOAD_CONTENT_TYPES = {
    "mp4": "video/mp4",
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "srt": "text/plain",
    "json": "application/json",
}

DEFAULT_CONTENT_TYPE = "application/octet-stream"


def build_storage_key(project_id: int, step: str, filename: str) -> str:
    """스토리지 키 경로를 생성합니다.

    형식: projects/{project_id}/{step}/{filename}
    예시: projects/42/tts/audio.mp3
    """
    return f"projects/{project_id}/{step}/{filename}"


def get_content_type(filename: str) -> str:
    """파일명 확장자로부터 Content-Type을 반환합니다.

    UPLOAD_CONTENT_TYPES에 없는 확장자는 application/octet-stream을 반환합니다.
    대소문자를 구분하지 않습니다.
    """
    ext = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""
    return UPLOAD_CONTENT_TYPES.get(ext, DEFAULT_CONTENT_TYPE)


def validate_presigned_expiry(seconds: int) -> int:
    """Presigned URL 만료 시간을 검증하고 유효 범위로 클램핑합니다.

    반환값: MIN_PRESIGNED_EXPIRY_SECONDS ~ MAX_PRESIGNED_EXPIRY_SECONDS 사이의 값
    """
    return max(MIN_PRESIGNED_EXPIRY_SECONDS, min(seconds, MAX_PRESIGNED_EXPIRY_SECONDS))


class StorageService:
    """Cloudflare R2용 S3 호환 스토리지 서비스입니다."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._client = None

    def _get_client(self):
        """boto3 클라이언트를 지연 초기화합니다."""
        if self._client is None:
            import boto3

            self._client = boto3.client(
                "s3",
                endpoint_url=self._endpoint,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
            )
        return self._client

    def upload_file(self, key: str, data: bytes, content_type: str) -> str:
        """R2에 파일을 업로드합니다.

        Returns:
            업로드된 파일의 스토리지 URL
        """
        client = self._get_client()
        client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return f"{self._endpoint}/{self._bucket}/{key}"

    def get_presigned_url(
        self, key: str, expires: int = DEFAULT_PRESIGNED_EXPIRY_SECONDS
    ) -> str:
        """Presigned 다운로드 URL을 생성합니다."""
        expires = validate_presigned_expiry(expires)
        client = self._get_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires,
        )

    def delete_file(self, key: str) -> None:
        """R2에서 파일을 삭제합니다."""
        client = self._get_client()
        client.delete_object(Bucket=self._bucket, Key=key)
