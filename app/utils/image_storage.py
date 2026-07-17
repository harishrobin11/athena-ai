from pathlib import Path
from uuid import uuid4
from datetime import datetime
import shutil

UPLOAD_ROOT = Path("storage/uploads")


class ImageStorage:

    @staticmethod
    def save_image(file, conversation_id: str):
        """
        Save uploaded image inside:
        storage/uploads/<conversation_id>/
        """

        conversation_id = str(conversation_id)
        conversation_dir = UPLOAD_ROOT / conversation_id
        conversation_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(file.filename).suffix.lower()

        filename = f"{uuid4().hex}{extension}"

        filepath = conversation_dir / filename

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "id": uuid4().hex,
            "filename": filename,
            "path": str(filepath),
            "uploaded_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def list_images(conversation_id: str):
        """
        Returns all images for a conversation.
        """

        conversation_id = str(conversation_id)
        conversation_dir = UPLOAD_ROOT / conversation_id

        if not conversation_dir.exists():
            return []

        images = []

        for image in sorted(conversation_dir.iterdir()):
            if image.is_file():
                images.append(str(image))

        return images

    @staticmethod
    def latest_image(conversation_id: str):
        """
        Returns newest uploaded image.
        """

        images = ImageStorage.list_images(conversation_id)

        if not images:
            return None

        return images[-1]

    @staticmethod
    def delete_image(path: str):

        file = Path(path)

        if file.exists():
            file.unlink()

    @staticmethod
    def delete_conversation_images(conversation_id: str):

        conversation_id = str(conversation_id)
        conversation_dir = UPLOAD_ROOT / conversation_id

        if not conversation_dir.exists():
            return

        shutil.rmtree(conversation_dir)

    @staticmethod
    def image_exists(path: str):

        return Path(path).exists()