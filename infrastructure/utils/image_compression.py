"""Compressão de imagens antes de irem pro Supabase Storage.

Fotos de celular têm 3-6 MB (12+ megapixels) e o storage encheu com poucas
imagens. Aqui cada imagem vira um JPEG de **1024 x 576 px (16:9)**, bem leve
(normalmente 40-120 KB):
  - girada conforme o EXIF (fotos de celular vêm "deitadas" com uma flag de
    orientação — sem isso a imagem ficaria de lado depois de remover o EXIF);
  - encaixada inteira num quadro 1024x576, sem cortar nada e sem ampliar: se a
    foto não for 16:9 (retrato, 4:3...), as laterais/bordas são preenchidas com
    a própria foto desfocada. Fotos quase 16:9 (±3%) apenas são redimensionadas;
  - convertida para JPEG progressivo com qualidade 78, reduzida em passos até
    ~150 KB se for preciso (ruído e texturas pesam mais);
  - sem metadados (EXIF): remove GPS/data/modelo do aparelho — são fotos de
    crianças, então não há motivo pra guardar localização.
"""
import io
from dataclasses import dataclass

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError

TARGET_WIDTH = 1024
TARGET_HEIGHT = 576
JPEG_QUALITY = 78
# Se a imagem passar disto, tenta qualidades menores (nunca abaixo de MIN_QUALITY).
SIZE_BUDGET_BYTES = 150 * 1024
MIN_QUALITY = 60
RATIO_TOLERANCE = 0.03

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


def _fit_16_9(img: Image.Image) -> Image.Image:
    """Devolve exatamente 1024x576 com a foto inteira (sem cortar nem ampliar)."""
    w, h = img.size
    target_ratio = TARGET_WIDTH / TARGET_HEIGHT
    if abs(w / h - target_ratio) / target_ratio <= RATIO_TOLERANCE:
        # já é (quase) 16:9: só redimensiona para o quadro, sem barras
        return img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.LANCZOS) if (w, h) != (TARGET_WIDTH, TARGET_HEIGHT) else img

    # primeiro plano: a foto inteira, reduzida para caber (nunca ampliada)
    scale = min(TARGET_WIDTH / w, TARGET_HEIGHT / h, 1.0)
    fg = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS) if scale < 1.0 else img

    # fundo: a mesma foto preenchendo o quadro (cover), desfocada e um pouco mais escura
    cover = max(TARGET_WIDTH / w, TARGET_HEIGHT / h)
    bg = img.resize((max(TARGET_WIDTH, round(w * cover)), max(TARGET_HEIGHT, round(h * cover))), Image.LANCZOS)
    left, top = (bg.width - TARGET_WIDTH) // 2, (bg.height - TARGET_HEIGHT) // 2
    bg = bg.crop((left, top, left + TARGET_WIDTH, top + TARGET_HEIGHT))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=24))
    bg = ImageEnhance.Brightness(bg).enhance(0.8)

    bg.paste(fg, ((TARGET_WIDTH - fg.width) // 2, (TARGET_HEIGHT - fg.height) // 2))
    return bg


def compress_image(
    content: bytes,
    quality: int = JPEG_QUALITY,
) -> CompressedImage:
    """Encaixa a imagem num quadro 1024x576 (16:9) e converte para JPEG. Levanta InvalidImageError
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

    img = _fit_16_9(img)

    out = io.BytesIO()
    q = quality
    while True:
        out.seek(0)
        out.truncate()
        img.save(out, format="JPEG", quality=q, optimize=True, progressive=True)
        if out.tell() <= SIZE_BUDGET_BYTES or q <= MIN_QUALITY:
            break
        q -= 6
    data = out.getvalue()

    return CompressedImage(
        content=data,
        mime_type="image/jpeg",
        width=img.width,
        height=img.height,
        original_size=len(content),
    )
