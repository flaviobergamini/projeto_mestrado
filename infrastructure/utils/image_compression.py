"""Compressão de imagens de diário antes de irem pro Supabase Storage.

Fotos de celular têm 3-6 MB (12+ megapixels) e o storage encheu com poucas
imagens. Aqui cada imagem é:
  - girada conforme o EXIF (fotos de celular vêm "deitadas" com uma flag de
    orientação — sem isso a imagem ficaria de lado depois de remover o EXIF);
  - reduzida para caber em 1920x1080 (1080x1920 se for retrato), sem NUNCA
    ampliar imagens menores que isso;
  - convertida para JPEG qualidade 80 (otimizado + progressivo), que é o ponto
    onde a perda de qualidade ainda é praticamente invisível a olho nu, mas o
    arquivo costuma cair ~85-95%;
  - sem metadados (EXIF): remove GPS/data/modelo do aparelho — são fotos de
    crianças, então não há motivo pra guardar localização.
"""
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_LONG_SIDE = 1920
MAX_SHORT_SIDE = 1080
JPEG_QUALITY = 80

# Proteção contra "decompression bomb": recusa imagens absurdamente grandes
# (o Pillow já avisa acima de ~89 MP; aqui vira erro explícito acima de 100 MP).
Image.MAX_IMAGE_PIXELS = 100_000_000


class InvalidImageError(ValueError):
    """Arquivo não é uma imagem legível."""


@dataclass
class CompressedImage:
    content: bytes
    mime_type: str
    width: int
    height: int
    original_size: int

    @property
    def size(self) -> int:
        return len(self.content)


def _target_box(width: int, height: int) -> tuple[int, int]:
    # Paisagem: 1920x1080; retrato: 1080x1920 — mesma "área" nos dois casos.
    if width >= height:
        return (MAX_LONG_SIDE, MAX_SHORT_SIDE)
    return (MAX_SHORT_SIDE, MAX_LONG_SIDE)


def compress_image(
    content: bytes,
    quality: int = JPEG_QUALITY,
) -> CompressedImage:
    """Redimensiona (sem ampliar) e converte para JPEG. Levanta InvalidImageError
    se o conteúdo não for uma imagem. GIFs animados viram só o 1º quadro."""
    try:
        img = Image.open(io.BytesIO(content))
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise InvalidImageError(f"Arquivo de imagem inválido: {e}") from e

    # Aplica a rotação do EXIF e descarta o resto dos metadados.
    img = ImageOps.exif_transpose(img)

    # JPEG não tem transparência: achata PNG/WebP/GIF com alfa sobre fundo branco.
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # thumbnail() só reduz (nunca amplia) e preserva a proporção.
    img.thumbnail(_target_box(*img.size), Image.LANCZOS)

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True, progressive=True)
    data = out.getvalue()

    return CompressedImage(
        content=data,
        mime_type="image/jpeg",
        width=img.width,
        height=img.height,
        original_size=len(content),
    )
