"""PDF do relatório do Kanban (ReportLab), no mesmo timbre do relatório de habilidades."""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from infrastructure.services.pdf_service import (
    _build_styles, _build_header, _footer_canvas, _escape, LIGHT, TEXT, MUTED,
)

STATUS_LABELS = {"todo": "A fazer", "doing": "Fazendo", "done": "Concluído", "archived": "Arquivado"}


def _fmt_date(iso: str | None) -> str:
    d = (iso or "")[:10]
    return f"{d[8:10]}/{d[5:7]}/{d[:4]}" if len(d) == 10 else ""


def _filters_text(f: dict) -> str:
    parts = ["Colunas: " + (", ".join(STATUS_LABELS.get(s, s) for s in f.get("statuses") or []) or "todas")]
    parts.append("Anos: " + (", ".join(f.get("grades") or []) or "todos"))
    if f.get("areas"):
        parts.append("Áreas: " + ", ".join(f["areas"]))
    if f.get("date_from") or f.get("date_to"):
        parts.append(f"Período: {_fmt_date(f.get('date_from')) or 'início'} a {_fmt_date(f.get('date_to')) or 'hoje'}")
    parts.append("com ações" if f.get("include_actions", True) else "sem ações (só resumo)")
    parts.append("com datas" if f.get("include_dates", True) else "sem datas")
    parts.append("com lançamentos das ações" if f.get("include_entries") else "sem lançamentos das ações")
    return " | ".join(parts)


def generate_kanban_report_pdf(report: dict, student_name: str) -> bytes:
    filters = report.get("filters", {})
    include_entries = bool(filters.get("include_entries"))
    include_actions = filters.get("include_actions", True)
    include_dates = filters.get("include_dates", True)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=2.0 * cm, bottomMargin=2.6 * cm,
        title=f"Kanban — {student_name}", author="Autism.iA", subject="Relatório do Kanban",
    )
    styles = _build_styles()
    small = ParagraphStyle("KSmall", fontName="Helvetica", fontSize=8.5, leading=11, textColor=TEXT)
    small_b = ParagraphStyle("KSmallB", parent=small, fontName="Helvetica-Bold")
    muted = ParagraphStyle("KMuted", parent=small, textColor=MUTED)

    story: list = []
    story.extend(_build_header(_escape(student_name), report.get("generated_at", ""), styles, subtitle="Relatório do Kanban"))
    story.append(Paragraph(_escape(_filters_text(filters)), muted))
    story.append(Spacer(1, 6))

    counts = report.get("counts", {})
    head = [STATUS_LABELS[s] for s in STATUS_LABELS if s in (filters.get("statuses") or STATUS_LABELS)]
    t = Table([head, [str(counts.get(s, 0)) for s in STATUS_LABELS if s in (filters.get("statuses") or STATUS_LABELS)]], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bdbdbd")),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    page_w = A4[0] - 3.6 * cm
    date_w = 2.3 * cm if include_dates else 0
    widths = [2.3 * cm, page_w - 2.3 * cm - 2.4 * cm - date_w, 2.4 * cm] + ([date_w] if include_dates else [])

    for group in report.get("groups", []):
        story.append(Paragraph(_escape(group["subject"]), styles["h1"]))
        for skill in group["skills"]:
            title = f"{skill['code']} — {skill['description']}" if skill.get("code") else "Ações sem habilidade"
            story.append(Paragraph(_escape(title), styles["h3"]))
            if not include_actions:
                # só o resumo da habilidade: quantas ações em cada coluna
                tally = {}
                for c in skill["cards"]:
                    tally[c["status"]] = tally.get(c["status"], 0) + 1
                story.append(Paragraph(" · ".join(f"{STATUS_LABELS.get(k, k)}: {tally[k]}" for k in STATUS_LABELS if k in tally), small))
                story.append(Spacer(1, 6))
                continue
            head = [Paragraph("Coluna", small_b), Paragraph("Ação", small_b), Paragraph("Responsável", small_b)]
            if include_dates:
                head.append(Paragraph("Atualizado", small_b))
            rows = [head]
            for c in skill["cards"]:
                row = [
                    Paragraph(STATUS_LABELS.get(c["status"], c["status"]), small_b),
                    Paragraph(_escape(c["title"]), small),
                    Paragraph(_escape(c.get("responsible_name") or ""), small),
                ]
                if include_dates:
                    row.append(Paragraph(_fmt_date(c.get("updated_at")), small))
                rows.append(row)
            tbl = Table(rows, colWidths=widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bdbdbd")),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
            ]))
            story.append(tbl)
            if include_entries:
                for c in skill["cards"]:
                    for e in c.get("entries", []):
                        reaction = f" — reação {e['reaction']}/5" if e.get("reaction") else ""
                        when = f"<b>{_fmt_date(e['entry_date'])}</b> · " if include_dates else ""
                        story.append(KeepTogether(Paragraph(
                            f"{when}{_escape(c['title'])}{reaction}: {_escape(e.get('text') or '')}", small)))
            story.append(Spacer(1, 6))

    if not report.get("groups"):
        story.append(Spacer(1, 10))
        story.append(Paragraph("Nenhuma ação corresponde aos filtros escolhidos.", styles["body"]))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bdbdbd"), spaceAfter=6))
    story.append(Paragraph("Documento gerado pelo sistema Autism.iA.", styles["confidential"]))
    doc.build(story, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
    return buf.getvalue()
