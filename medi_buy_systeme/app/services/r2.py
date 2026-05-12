import boto3
import time
from app.config import Config

_creatives_cache = None
_creatives_cache_time = 0
CACHE_TTL = 30  # seconds


class R2Client:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=Config.R2_ENDPOINT,
            aws_access_key_id=Config.R2_ACCESS_KEY_ID,
            aws_secret_access_key=Config.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        self.bucket = Config.R2_BUCKET
        self.public_url = Config.R2_PUBLIC_URL

    def list_creatives(self, use_cache=True):
        global _creatives_cache, _creatives_cache_time
        if use_cache and _creatives_cache and (time.time() - _creatives_cache_time) < CACHE_TTL:
            return _creatives_cache

        response = self.s3.list_objects_v2(Bucket=self.bucket)
        files = response.get("Contents", [])
        result = [
            {
                "key": f["Key"],
                "url": f"{self.public_url}/{f['Key']}",
                "size_kb": round(f["Size"] / 1024, 1),
                "type": self._guess_type(f["Key"]),
            }
            for f in files
        ]

        _creatives_cache = result
        _creatives_cache_time = time.time()
        return result

    def _guess_type(self, key):
        ext = key.lower().split(".")[-1]
        if ext in ("jpg", "jpeg", "png", "gif", "webp", "avif"):
            return "image"
        if ext in ("mp4", "webm", "mov", "avi"):
            return "video"
        return "file"

    def upload_creative(self, local_path, key):
        self.s3.upload_file(local_path, self.bucket, key)
        return f"{self.public_url}/{key}"

    def get_creative_url(self, key):
        return f"{self.public_url}/{key}"

    def delete_creative(self, key):
        self.s3.delete_object(Bucket=self.bucket, Key=key)