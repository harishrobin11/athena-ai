import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from typing import Optional
from abc import ABC, abstractmethod

class CloudStorageProvider(ABC):
    @abstractmethod
    def upload_file(self, file_content: bytes, bucket: str, object_name: str, content_type: str) -> str:
        pass

    def get_presigned_url(self, bucket: str, object_name: str, expiration: int = 3600) -> str:
        pass

    @abstractmethod
    def get_file_bytes(self, bucket: str, object_name: str) -> bytes:
        pass

    @abstractmethod
    def delete_file(self, bucket: str, object_name: str) -> bool:
        pass


class Boto3Storage(CloudStorageProvider):
    def __init__(self):
        # We default to the local MinIO instance configured in docker-compose
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL", "http://127.0.0.1:9000")
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID", "athena_admin")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "athena_password")
        self.region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )

    def upload_file(self, file_content: bytes, bucket: str, object_name: str, content_type: str = "application/octet-stream") -> str:
        """
        Uploads bytes directly to the specified bucket.
        Returns the object_name (key) to be stored in the database.
        """
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=object_name,
                Body=file_content,
                ContentType=content_type
            )
            return object_name
        except ClientError as e:
            print(f"Failed to upload to S3: {e}")
            raise Exception("Storage upload failed")

    def get_presigned_url(self, bucket: str, object_name: str, expiration: int = 3600) -> str:
        """
        Generates a presigned URL to securely download/view the file directly from the browser.
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            print(f"Failed to generate presigned URL: {e}")
            return ""

    def get_file_bytes(self, bucket: str, object_name: str) -> bytes:
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=object_name)
            return response['Body'].read()
        except ClientError as e:
            print(f"Failed to get file from S3: {e}")
            raise FileNotFoundError(f"{object_name} not found.")

    def delete_file(self, bucket: str, object_name: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=object_name)
            return True
        except ClientError as e:
            print(f"Failed to delete file from S3: {e}")
            return False

# Global dependency injection provider
storage_service = Boto3Storage()
