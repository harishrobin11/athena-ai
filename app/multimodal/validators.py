from pathlib import Path

SUPPORTED_IMAGE_TYPES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

MAX_IMAGE_SIZE_MB = 10


def validate_image(image_path: str):
    path = Path(image_path)

    extension = path.suffix.lower()

    if extension not in SUPPORTED_IMAGE_TYPES:
        raise ValueError(
            f"Unsupported image type: {extension}"
        )

    return True