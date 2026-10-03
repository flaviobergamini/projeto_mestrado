"""PDF do relatório de habilidades BNCC (ReportLab), no mesmo timbre dos demais PDFs."""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from infrastructure.services.pdf_service import (
    _build_styles, _build_header, _footer_canvas, _escape, PRIMARY, ACCENT, LIGHT, TEXT, MUTED,
)


def _filters_text(f: dict) -> str:
    parts = ["Anos: " + (", ".join(f.get("grades") or []) or "todos")]
    if f.get("areas"):
        parts.append("Áreas: " + ", ".join(f["areas"]))
    lo, hi = f.get("min_score"), f.get("max_score")
    if lo is not None or hi is not None:
        parts.append(f"Notas de {lo if lo is not None else 0} a {hi if hi is not None else 5}")
    if f.get("only_with_observation"):
        parts.append("somente com observação")
    parts.append("com observações" if f.get("include_observations") else "sem observações")
    if f.get("query"):
        parts.append(f"busca: {f['query']}")
    return " | ".join(parts)


def generate_skill_report_pdf(report: dict, student_name: str) -> bytes:
    content = report.get("content") or {}
    summary = content.get("summary", {})
    include_obs = bool(content.get("filters", {}).get("include_observations"))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=2.0 * cm, bottomMargin=2.6 * cm,
        title=f"{report.get('title', 'Habilidades BNCC')} — {student_name}", author="Autism.iA",
        subject="Relatório de habilidades BNCC",
    )
    styles = _build_styles()
    small = ParagraphStyle("SmallCell", fontName="Helvetica", fontSize=8.5, leading=11, textColor=TEXT)
    small_b = ParagraphStyle("SmallCellB", parent=small, fontName="Helvetica-Bold")
    muted = ParagraphStyle("MutedCell", parent=small, textColor=MUTED)

    story: list = []
    story.extend(_build_header(
        _escape(student_name), content.get("generated_at") or report.get("created_at") or "", styles,
        subtitle="Relatório de habilidades BNCC",
    ))
    story.append(Paragraph(_escape(report.get("title", "")), styles["h2"]))
    story.append(Paragraph(_escape(_filters_text(content.get("filters", {}))), muted))
    story.append(Spacer(1, 6))

    by = summary.get("by_score", {})
    totals = [["Habilidades", "Média"] + [f"Nota {n}" for n in range(6)],
              [str(summary.get("total", 0)), str(summary.get("average", 0))] + [str(by.get(str(n), 0)) for n in range(6)]]
    t = Table(totals, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bdbdbd")),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    page_w = A4[0] - 3.6 * cm
    widths = [2.4 * cm, page_w - 2.4 * cm - 1.3 * cm - (5.2 * cm if include_obs else 0), 1.3 * cm] + ([5.2 * cm] if include_obs else [])

    for group in content.get("groups", []):
        story.append(Paragraph(_escape(group["grade"]), styles["h1"]))
        for area in group["areas"]:
            story.append(Paragraph(_escape(area["area"]), styles["h3"]))
            head = [Paragraph("Código", small_b), Paragraph("Habilidade", small_b), Paragraph("Nota", small_b)]
            if include_obs:
                head.append(Paragraph("Observação", small_b))
            rows = [head]
            for sk in area["skills"]:
                row = [Paragraph(_escape(sk["code"]), small), Paragraph(_escape(sk["description"]), small),
                       Paragraph(f"{sk['score']}/5", small_b)]
                if include_obs:
                    row.append(Paragraph(_escape(sk.get("observation", "")), small))
                rows.append(row)
            tbl = Table(rows, colWidths=widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bdbdbd")),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 4))

    if not content.get("groups"):
        story.append(Spacer(1, 10))
        story.append(Paragraph("Nenhuma habilidade corresponde aos filtros escolhidos.", styles["body"]))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bdbdbd"), spaceAfter=6))
    story.append(Paragraph(
        "Notas de 0 a 5 atribuídas pela equipe pedagógica (0 = habilidade ainda não consolidada). "
        "Documento gerado pelo sistema Autism.iA.", styles["confidential"]))
    doc.build(story, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
    return buf.getvalue()
