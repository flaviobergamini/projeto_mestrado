"""Extração tradicional (sem IA, sem OCR) do texto de um PDF."""
import io
import re

MAX_PAGES = 400


class PdfTextError(Exception):
    """PDF ilegível (corrompido, protegido por senha)."""


def extract_pdf_text(content: bytes) -> str:
    """Texto de todas as páginas, na ordem. PDF só de imagem (digitalizado) devolve texto vazio."""
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError

    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted and not reader.decrypt(""):
            raise PdfTextError("PDF protegido por senha.")
        pages = []
        for page in list(reader.pages)[:MAX_PAGES]:
            pages.append(page.extract_text() or "")
    except PdfTextError:
        raise
    except (PyPdfError, ValueError, KeyError, OSError) as exc:
        raise PdfTextError(f"PDF ilegível: {exc}") from exc
    text = "\n\n".join(pages)
    return re.sub(r"[ \t]+\n", "\n", text).strip()
