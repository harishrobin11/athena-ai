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

    if not path.exists():
        raise FileNotFoundError(
            f"{image_path} not found."
        )

    extension = path.suffix.lower()

    if extension not in SUPPORTED_IMAGE_TYPES:
        raise ValueError(
            f"Unsupported image type: {extension}"
        )

    size_mb = path.stat().st_size / (1024 * 1024)

    if size_mb > MAX_IMAGE_SIZE_MB:
        raise ValueError(
            f"Image exceeds {MAX_IMAGE_SIZE_MB} MB."
        )

    return True