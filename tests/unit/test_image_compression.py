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


def test_every_image_becomes_exactly_1024x576_jpeg():
    for size in ((4000, 3000), (3000, 4000), (1920, 1080), (640, 480), (800, 800)):
        result = compress_image(_noise_image(size))
        assert result.mime_type == "image/jpeg"
        assert (result.width, result.height) == (1024, 576), size
        out = _open(result.content)
        assert out.format == "JPEG" and out.size == (1024, 576)


def test_large_photo_is_much_lighter_than_the_original():
    original = _noise_image((4000, 3000))
    result = compress_image(original)
    assert result.size < result.original_size * 0.05
    assert result.size <= 160 * 1024  # limite de ~150 KB mesmo com ruído (pior caso)


def test_portrait_photo_is_kept_whole_with_blurred_sides():
    img = Image.new("RGB", (600, 1000), (255, 0, 0))   # retrato todo vermelho
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    out = _open(compress_image(buf.getvalue()).content).convert("RGB")
    cx = out.getpixel((512, 288))
    assert cx[0] > 200 and cx[1] < 60       # centro: a foto vermelha
    # a foto ocupa 346x576 no centro (1000 -> 576); fora dela há o fundo desfocado, não bordas pretas
    side = out.getpixel((60, 288))
    assert side[0] > 100                    # ainda avermelhado (desfoque da própria foto), não preto


def test_small_image_is_never_upscaled_inside_the_frame():
    img = Image.new("RGB", (200, 200), (0, 200, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    out = _open(compress_image(buf.getvalue()).content).convert("RGB")
    assert out.size == (1024, 576)
    # a imagem 200x200 fica no centro com o tamanho original (100px de cada lado do centro)
    assert out.getpixel((512, 288))[1] > 150


def test_png_with_transparency_becomes_jpeg_on_white():
    img = Image.new("RGBA", (200, 200), (255, 0, 0, 0))  # totalmente transparente
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = compress_image(buf.getvalue())
    out = _open(result.content)
    assert out.format == "JPEG" and out.mode == "RGB"
    r, g, b = out.getpixel((512, 288))  # centro do quadro 1024x576, onde fica a imagem de 200x200
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
    assert (out.width, out.height) == (1024, 576)
    # 400x200 com rotação EXIF vira 200x400 (em pé): o centro é a foto, as laterais o fundo desfocado
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
