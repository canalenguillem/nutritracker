from app.services.food_analysis import MealPhoto

ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Leading bytes that identify each format, so a renamed file is caught.
SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"RIFF", "image/webp"),
)


class InvalidImageError(Exception):
    pass


class ImageTooLargeError(Exception):
    pass


def detect_media_type(content: bytes) -> str | None:
    for signature, media_type in SIGNATURES:
        if content.startswith(signature):
            if media_type == "image/webp" and content[8:12] != b"WEBP":
                continue
            return media_type
    return None


def validate_photo(content: bytes, max_bytes: int) -> MealPhoto:
    if not content:
        raise InvalidImageError("The image is empty.")

    if len(content) > max_bytes:
        raise ImageTooLargeError(str(len(content)))

    # Trust the bytes rather than the declared type or the file name.
    media_type = detect_media_type(content)
    if media_type is None:
        raise InvalidImageError("The file is not a JPEG, PNG or WebP image.")

    return MealPhoto(content=content, media_type=media_type)
