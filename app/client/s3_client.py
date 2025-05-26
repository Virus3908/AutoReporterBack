from urllib.parse import urljoin

import boto3
from botocore.client import Config

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("s3")


class S3Client:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version="s3v4"),
            region_name=settings.s3_region,
        )
        self.bucket = settings.s3_bucket
        self.endpoint = settings.s3_endpoint

    def check_connection(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception as e:
            logger.error(f"S3 Connection failed: {e}")

    def upload_file(self, file_path: str, object_name: str) -> str:
        self.client.upload_file(file_path, self.bucket, object_name)
        return urljoin(f"{self.endpoint}/{self.bucket}/", object_name)


s3_client = S3Client()
