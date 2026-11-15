from types import SimpleNamespace

from api.document_routes import _is_pdf


def _file(content_type):
    return SimpleNamespace(content_type=content_type)


def test_only_real_pdfs_are_accepted():
    assert _is_pdf(_file("application/pdf"), b"%PDF-1.7 ...") is True
    assert _is_pdf(_file("application/pdf"), b"MZ\x90\x00 not a pdf") is False   # tipo declarado não basta
    assert _is_pdf(_file("image/png"), b"%PDF-1.7 ...") is False
