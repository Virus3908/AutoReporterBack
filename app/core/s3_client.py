import boto3
from botocore.client import Config
from app.config.settings import settings


class S3Client:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version='s3v4'),
            region_name="us-east-1"
        )
        self.bucket = settings.s3_bucket
        self.endpoint = settings.s3_endpoint
        
    def check_connection(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return True
        except Exception as e:
            print(f"S3 Connection failed: {e}")
            return False

    def upload_file(self, file_path: str, object_name: str) -> str:
        self.client.upload_file(file_path, self.bucket, object_name)
        return f"{self.endpoint}/{self.bucket}/{object_name}"



    def download_file(self, object_name: str, dest_path: str):
        self.client.download_file(self.bucket, object_name, dest_path)

    def get_url(self, object_name: str) -> str:
        return f"{settings.s3_endpoint}/{self.bucket}/{object_name}"
    
s3_client = S3Client()