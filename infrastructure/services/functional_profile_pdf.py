"""PDF do perfil funcional (ReportLab), no mesmo timbre dos demais PDFs."""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from core.constants.functional_profile import LEVEL_SCALE
from infrastructure.services.pdf_service import _build_styles, _build_header, _footer_canvas, _escape

# mesmos rótulos da tela (messages/pt.json)
_LISTS = (("strengths", "Pontos fortes"), ("needs", "Necessidades"), ("supports", "Apoios"))
_LEVELS = {1: "1 · Apoio muito substancial", 2: "2 · Apoio substancial", 3: "3 · Apoio moderado", 4: "4 · Apoio pontual", 5: "5 · Independente"}


def _date(value) -> str:
    """AAAA-MM-DD (ou ISO com hora) -> DD/MM/AAAA."""
    text = str(value or "")[:10]
    return f"{text[8:10]}/{text[5:7]}/{text[:4]}" if len(text) == 10 else ""


def generate_functional_profile_pdf(profile: dict, student_name: str) -> bytes:
    content = profile.get("content") or {}
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=2.0 * cm, bottomMargin=2.6 * cm,
        title=f"{profile.get('title') or 'Perfil funcional'} — {student_name}", author="Autism.iA", subject="Perfil funcional",
    )
    styles = _build_styles()
    body = styles["body"]
    story: list = list(_build_header(_escape(student_name), profile.get("created_at") or "", styles, subtitle="Perfil funcional"))

    story.append(Paragraph(_escape(profile.get("title") or "Perfil funcional"), styles["h2"]))
    meta = ["Origem: " + ("gerado por IA" if profile.get("origin") == "ai" else "preenchido manualmente")]
    start, end = _date(profile.get("period_start")), _date(profile.get("period_end"))
    if start or end:
        meta.append(f"Período: {start or '?'} a {end or '?'}")
    if profile.get("created_by"):
        meta.append(f"Criado por {profile['created_by']} em {_date(profile.get('created_at'))}")
    if profile.get("edited_by"):
        meta.append(f"Editado por {profile['edited_by']}")
    if profile.get("average_level"):
        meta.append(f"Média: {profile['average_level']}")
    story.append(Paragraph(_escape(" | ".join(meta)), styles["confidential"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Síntese", styles["h3"]))
    story.append(Paragraph(_escape(content.get("summary") or "Sem síntese.").replace("\n", "<br/>"), body))

    for d in content.get("domains") or []:
        story.append(Paragraph(_escape(d.get("label") or ""), styles["h1"]))
        level = d.get("level")
        story.append(Paragraph(f"<b>Nível:</b> {_LEVELS.get(level, 'Sem evidência')}", body))
        if d.get("description"):
            story.append(Paragraph(_escape(d["description"]).replace("\n", "<br/>"), body))
        for key, title in _LISTS:
            items = d.get(key) or []
            if items:
                story.append(Paragraph(title, styles["h3"]))
                story.extend(Paragraph(f"• {_escape(item)}", body) for item in items)
        if d.get("bncc_references"):
            story.append(Paragraph(f"<b>Habilidades BNCC relacionadas:</b> {_escape(', '.join(d['bncc_references']))}", body))

    if content.get("evidence"):
        story.append(Paragraph("Fontes consideradas", styles["h3"]))
        story.extend(Paragraph(f"• {_escape(item)}", body) for item in content["evidence"])

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bdbdbd"), spaceAfter=6))
    story.append(Paragraph(_escape(f"Escala de níveis: {LEVEL_SCALE}."), styles["confidential"]))
    story.append(Paragraph(
        "O perfil funcional é uma proposta de apoio pedagógico, não um laudo. Documento com dados pessoais: "
        "compartilhe somente com quem precisa. Gerado pelo sistema Autism.iA.", styles["confidential"]))
    doc.build(story, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
    return buf.getvalue()
