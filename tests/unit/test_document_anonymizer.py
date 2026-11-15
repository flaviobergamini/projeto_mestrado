import io
from datetime import date

from core.services.document_anonymizer import anonymize_text, chunk_text
from infrastructure.utils.pdf_text import PdfTextError, extract_pdf_text

SAMPLE = """LAUDO NEUROPSICOLÓGICO
Nome: Alvina Almeida Bastos Bisneta
Data de nascimento: 14/03/2016
Mãe: Joana Pereira Bisneta
CPF: 123.456.789-09  RG: 12.345.678-9
Endereço: Rua das Flores, 123, Centro - Piranguinho/MG - CEP 37508-000
Telefone: (35) 99876-5432   E-mail: joana.bisneta@exemplo.com

Alvina frequenta a Escola Municipal Almerinda Valente de Lima, sob orientação da professora Estefany Guimarães.
A avaliação foi realizada pela Dra. Carla Menezes (CRP 04/12345) em 10/10/2026.
Alvina apresenta dificuldade nas transições. Segundo Joana, a criança dorme mal.
"""

ID_NAMES = {"Escola Municipal Almerinda Valente de Lima": "school-uuid"}
PERSON_NAMES = {"Alvina Almeida Bastos Bisneta": "student-uuid", "Estefany Guimarães dos Reis Dias": "teacher-uuid"}


def _run(text=SAMPLE):
    return anonymize_text(
        text, id_names=ID_NAMES, person_names=PERSON_NAMES, guardian_names=["Joana Pereira Bisneta"],
        birth_date=date(2016, 3, 14),
    )


def test_known_names_become_the_system_identifiers():
    out = _run()
    assert "student-uuid" in out and "school-uuid" in out
    assert "teacher-uuid" in out                      # "Estefany" sozinho também é trocado
    for real in ("Alvina", "Almerinda", "Estefany", "Joana", "Pereira"):
        assert real not in out


def test_documents_contacts_address_and_registry_are_removed():
    out = _run()
    for leaked in ("123.456.789-09", "12.345.678-9", "99876-5432", "joana.bisneta@exemplo.com", "37508-000",
                   "Rua das Flores", "14/03/2016", "Carla Menezes", "04/12345"):
        assert leaked not in out, leaked
    for marker in ("[CPF]", "[E-MAIL]", "[TELEFONE]", "[ENDEREÇO]", "[PROFISSIONAL]", "[DATA DE NASCIMENTO]", "[RESPONSÁVEL]"):
        assert marker in out, marker


def test_clinical_content_is_kept():
    out = _run()
    assert "dificuldade nas transições" in out
    assert "10/10/2026" in out                         # data da avaliação não é dado de nascimento
    assert "dorme mal" in out


def test_unknown_name_in_a_labelled_field_is_masked():
    out = anonymize_text("Nome: Fulano de Tal\nObservações: tudo bem\nPai: Beltrano Souza")
    assert "Fulano" not in out and "Beltrano" not in out
    assert "tudo bem" in out


def test_name_without_accents_and_across_a_line_break():
    out = anonymize_text("A aluna Alvina Almeida\nBastos Bisneta chegou. Tambem Estefany Guimaraes.",
                         person_names=PERSON_NAMES)
    assert "Almeida" not in out and "Guimaraes" not in out


def test_empty_and_chunking():
    assert anonymize_text("") == ""
    assert chunk_text("") == []
    chunks = chunk_text("Parágrafo um. " * 400)
    assert len(chunks) > 1 and all(len(c) <= 1300 for c in chunks)


def _pdf(text: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    for line in text.splitlines():
        c.drawString(50, y, line)
        y -= 16
    c.save()
    return buf.getvalue()


def test_pdf_text_is_extracted_without_ai():
    text = extract_pdf_text(_pdf("Relatorio escolar\nAlvina apresenta progresso"))
    assert "Relatorio escolar" in text and "progresso" in text


def test_blank_pdf_has_no_text_and_garbage_is_an_error():
    assert extract_pdf_text(_pdf("")) == ""
    try:
        extract_pdf_text(b"%PDF-1.4 isto nao e um pdf")
    except PdfTextError:
        return
    raise AssertionError("deveria falhar")


def test_guardian_names_accept_strings_and_dicts():
    from infrastructure.services.document_ingestion import _guardian_names
    assert _guardian_names('["Joana Pereira", {"name": "Carlos Souza", "kinship": "pai"}, ""]') == ["Joana Pereira", "Carlos Souza"]
    assert _guardian_names("Maria Lima") == ["Maria Lima"]
    assert _guardian_names(None) == []


def test_documents_never_enter_the_rag_by_default():
    from infrastructure.services.rag_service import RagService
    assert "student_documents" in RagService.VALID_SOURCES
    assert "student_documents" not in RagService.DEFAULT_SOURCES   # só quando a fonte é marcada de propósito
