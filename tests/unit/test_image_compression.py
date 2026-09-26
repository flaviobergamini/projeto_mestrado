import io

import pytest
from PIL import Image

from infrastructure.utils.image_compression import (
    InvalidImageError,
    compress_image,
)


def _noise_image(size, mode="RGB", fmt="JPEG"):
    """Imagem com ruído pseudo-aleatório (comprime mal, como foto de verdade)."""
    import os
    w, h = size
    img = Image.frombytes("RGB", size, os.urandom(w * h * 3))
    if mode != "RGB":
        img = img.convert(mode)
    buf = io.BytesIO()
    img.save(buf, format=fmt, **({"quality": 95} if fmt == "JPEG" else {}))
    return buf.getvalue()


def _open(data):
    return Image.open(io.BytesIO(data))


def test_large_landscape_is_resized_to_1920x1080_box():
    result = compress_image(_noise_image((4000, 3000)))
    assert result.mime_type == "image/jpeg"
    assert result.width <= 1920 and result.height <= 1080
    # 4000x3000 (4:3) -> limitado pela altura: 1440x1080
    assert (result.width, result.height) == (1440, 1080)
    assert result.size < result.original_size


def test_portrait_uses_rotated_box():
    result = compress_image(_noise_image((3000, 4000)))
    assert (result.width, result.height) == (1080, 1440)


def test_small_image_is_never_upscaled():
    result = compress_image(_noise_image((640, 480)))
    assert (result.width, result.height) == (640, 480)


def test_png_with_transparency_becomes_jpeg_on_white():
    img = Image.new("RGBA", (200, 200), (255, 0, 0, 0))  # totalmente transparente
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = compress_image(buf.getvalue())
    out = _open(result.content)
    assert out.format == "JPEG" and out.mode == "RGB"
    r, g, b = out.getpixel((100, 100))
    assert r > 240 and g > 240 and b > 240  # fundo branco


def test_exif_orientation_is_applied_and_metadata_dropped():
    img = Image.new("RGB", (400, 200), (10, 120, 200))
    exif = Image.Exif()
    exif[0x0112] = 6  # rotacionar 90° horário ao exibir
    exif[0x010F] = "AparelhoTeste"
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    result = compress_image(buf.getvalue())
    out = _open(result.content)
    assert (out.width, out.height) == (200, 400)  # ficou em pé
    assert not out.getexif()  # EXIF removido


def test_invalid_bytes_raise_invalid_image_error():
    with pytest.raises(InvalidImageError):
        compress_image(b"isto nao e uma imagem")


def test_gif_is_converted_to_jpeg():
    img = Image.new("P", (50, 50))
    buf = io.BytesIO()
    img.save(buf, format="GIF")
    result = compress_image(buf.getvalue())
    assert _open(result.content).format == "JPEG"
