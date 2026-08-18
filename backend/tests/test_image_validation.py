import pytest

from app.services.image_validation import (
    ImageTooLargeError,
    InvalidImageError,
    detect_media_type,
    validate_photo,
)

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
WEBP = b"RIFF" + b"0000" + b"WEBP" + b"0" * 64
ONE_MB = 1024 * 1024


def test_each_supported_format_is_recognised() -> None:
    assert detect_media_type(JPEG) == "image/jpeg"
    assert detect_media_type(PNG) == "image/png"
    assert detect_media_type(WEBP) == "image/webp"


def test_a_photo_is_typed_by_its_content() -> None:
    photo = validate_photo(PNG, ONE_MB)

    assert photo.media_type == "image/png"
    assert photo.content == PNG


def test_a_renamed_file_does_not_pass_as_an_image() -> None:
    with pytest.raises(InvalidImageError):
        validate_photo(b"GIF89a" + b"0" * 64, ONE_MB)


def test_a_riff_container_that_is_not_webp_is_refused() -> None:
    with pytest.raises(InvalidImageError):
        validate_photo(b"RIFF" + b"0000" + b"WAVE" + b"0" * 64, ONE_MB)


def test_an_empty_file_is_refused() -> None:
    with pytest.raises(InvalidImageError):
        validate_photo(b"", ONE_MB)


def test_a_photo_over_the_limit_is_refused() -> None:
    with pytest.raises(ImageTooLargeError):
        validate_photo(JPEG + b"0" * ONE_MB, ONE_MB)


def test_two_photos_have_different_digests() -> None:
    assert validate_photo(JPEG, ONE_MB).digest != validate_photo(PNG, ONE_MB).digest
