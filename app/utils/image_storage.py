from uuid import uuid4
from datetime import datetime
from app.services.storage_service import storage_service

class ImageStorage:
    @staticmethod
    def save_image(file, conversation_id: str):
        """
        Save uploaded image inside S3 bucket athena-images/<conversation_id>/<filename>
        """
        conversation_id = str(conversation_id)
        
        # Read file bytes directly (FastAPI UploadFile)
        file_bytes = file.file.read()
        file.file.seek(0)  # Reset pointer just in case

        # We keep the extension
        import os
        from pathlib import Path
        extension = Path(file.filename).suffix.lower()
        filename = f"{uuid4().hex}{extension}"
        
        # S3 object key
        object_key = f"{conversation_id}/{filename}"
        
        # Upload to MinIO
        storage_service.upload_file(
            file_content=file_bytes,
            bucket="athena-images",
            object_name=object_key,
            content_type=file.content_type or "image/jpeg"
        )

        return {
            "id": uuid4().hex,
            "filename": filename,
            "path": object_key,
            "uploaded_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def list_images(conversation_id: str):
        """
        Returns all images for a conversation from S3.
        """
        conversation_id = str(conversation_id)
        prefix = f"{conversation_id}/"
        
        try:
            # Note: This uses the underlying boto3 client directly for listing
            response = storage_service.s3_client.list_objects_v2(
                Bucket="athena-images", 
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
                
            images = []
            for obj in response['Contents']:
                # The object key is something like "conv_id/filename.jpg"
                key = obj['Key']
                filename = key.split('/')[-1]
                
                images.append({
                    "id": filename.split('.')[0], # rough id
                    "filename": filename,
                    "path": key,
                    "uploaded_at": obj['LastModified'].isoformat(),
                })
            return images
        except Exception as e:
            print(f"Error listing images from S3: {e}")
            return []

    @staticmethod
    def latest_image(conversation_id: str):
        images = ImageStorage.list_images(conversation_id)
        if not images:
            return None
        # Sort by uploaded_at descending
        images.sort(key=lambda x: x["uploaded_at"], reverse=True)
        return images[0]["path"]

    @staticmethod
    def delete_image(path: str):
        storage_service.delete_file(bucket="athena-images", object_name=path)

    @staticmethod
    def delete_conversation_images(conversation_id: str):
        images = ImageStorage.list_images(conversation_id)
        for image in images:
            ImageStorage.delete_image(image["path"])

    @staticmethod
    def image_exists(path: str):
        try:
            storage_service.s3_client.head_object(Bucket="athena-images", Key=path)
            return True
        except:
            return False