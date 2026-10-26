import io

import pytest
from PIL import Image

from app.services.vision.image_search import (
    ImageValidationError,
    MultimodalImageSearchEngine,
)


def test_image_validation_empty_bytes():
    engine = MultimodalImageSearchEngine()
    with pytest.raises(ImageValidationError, match="empty"):
        engine.validate_upload(b"")


def test_image_validation_disallowed_extension():
    engine = MultimodalImageSearchEngine()
    with pytest.raises(ImageValidationError, match="Invalid image extension"):
        engine.validate_upload(b"some content", filename="malicious.exe")


def test_image_validation_corrupted_file():
    engine = MultimodalImageSearchEngine()
    with pytest.raises(ImageValidationError, match="not a valid"):
        engine.validate_upload(b"not an image byte stream", filename="test.jpg")


def test_image_validation_valid_png():
    engine = MultimodalImageSearchEngine()
    # Create valid 100x100 PNG in memory
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    val_bytes = buf.getvalue()

    validated = engine.validate_upload(val_bytes, filename="chair.png")
    assert validated.size == (100, 100)


def test_image_feature_extraction():
    engine = MultimodalImageSearchEngine()
    img = Image.new("RGB", (100, 100), color="green")
    features = engine.extract_image_features(img)
    assert features is not None
    assert len(features) > 0
