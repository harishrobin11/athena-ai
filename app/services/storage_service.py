import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError, EndpointConnectionError
import requests
from typing import Optional
from abc import ABC, abstractmethod
import datetime

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

class LocalStorage(CloudStorageProvider):
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/storage"))
        os.makedirs(self.base_dir, exist_ok=True)
        # Mock s3_client to avoid breaking image_storage.py which accesses it directly
        class MockS3Client:
            def list_objects_v2(self, Bucket, Prefix):
                bucket_dir = os.path.join(self.base_dir, Bucket)
                if not os.path.exists(bucket_dir):
                    return {}
                contents = []
                for root, dirs, files in os.walk(bucket_dir):
                    for file in files:
                        path = os.path.relpath(os.path.join(root, file), bucket_dir)
                        if path.startswith(Prefix):
                            contents.append({
                                'Key': path,
                                'LastModified': datetime.datetime.now()
                            })
                if contents:
                    return {'Contents': contents}
                return {}
            def head_object(self, Bucket, Key):
                path = os.path.join(self.base_dir, Bucket, Key)
                if not os.path.exists(path):
                    raise ClientError({'Error': {'Code': '404'}}, 'head_object')
                return True
        self.s3_client = MockS3Client()
        self.s3_client.base_dir = self.base_dir

    def _get_path(self, bucket: str, object_name: str) -> str:
        safe_object = os.path.normpath(f"/{object_name}").lstrip('/')
        return os.path.join(self.base_dir, bucket, safe_object)

    def upload_file(self, file_content: bytes, bucket: str, object_name: str, content_type: str = "application/octet-stream") -> str:
        path = self._get_path(bucket, object_name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(file_content)
        return object_name

    def get_presigned_url(self, bucket: str, object_name: str, expiration: int = 3600) -> str:
        return f"/files/{bucket}/{object_name}"

    def get_file_bytes(self, bucket: str, object_name: str) -> bytes:
        path = self._get_path(bucket, object_name)
        try:
            with open(path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"{object_name} not found.")

    def delete_file(self, bucket: str, object_name: str) -> bool:
        path = self._get_path(bucket, object_name)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

class Boto3Storage(CloudStorageProvider):
    def __init__(self):
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
        try:
            try:
                self.s3_client.head_bucket(Bucket=bucket)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404' or error_code == 'NoSuchBucket':
                    self.s3_client.create_bucket(Bucket=bucket)
                else:
                    raise e

            self.s3_client.put_object(
                Bucket=bucket,
                Key=object_name,
                Body=file_content,
                ContentType=content_type
            )
            return object_name
        except ClientError as e:
            print(f"Failed to upload to S3: {e}")
            raise Exception(f"Storage upload failed: {e}")

    def get_presigned_url(self, bucket: str, object_name: str, expiration: int = 3600) -> str:
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

def get_storage_provider():
    try:
        requests.get(os.getenv("S3_ENDPOINT_URL", "http://127.0.0.1:9000"), timeout=1)
        return Boto3Storage()
    except Exception:
        print("MinIO is unavailable. Falling back to LocalStorage.")
        return LocalStorage()

storage_service = get_storage_provider()
