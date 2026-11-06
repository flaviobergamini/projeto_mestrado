"""PDF do relatório do Kanban (ReportLab), no mesmo timbre do relatório de habilidades.

Uma tabela por coluna do quadro (A fazer, Fazendo, Concluído, Arquivado). Em cada tabela as ações vêm agrupadas pela
habilidade e, logo abaixo de cada ação, os lançamentos do diário dela."""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from infrastructure.services.pdf_service import (
    _build_styles, _build_header, _footer_canvas, _escape, LIGHT, TEXT, MUTED,
)

STATUS_LABELS = {"todo": "A fazer", "doing": "Fazendo", "done": "Concluído", "archived": "Arquivado"}
GRID = colors.HexColor("#bdbdbd")


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
    parts.append("com diários das ações" if f.get("include_entries", True) else "sem diários das ações")
    return " | ".join(parts)


def _skill_title(c: dict) -> str:
    base = f"{c['skill_code']} — {c.get('skill_description') or ''}" if c.get("skill_code") else "Ações sem habilidade"
    context = " · ".join(x for x in (c.get("skill_grade"), c.get("skill_area")) if x)
    return f"{base} ({context})" if context else base


def generate_kanban_report_pdf(report: dict, student_name: str) -> bytes:
    filters = report.get("filters", {})
    include_entries = filters.get("include_entries", True)
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
    entry_style = ParagraphStyle("KEntry", parent=small, fontSize=8, leading=10.5, leftIndent=8, textColor=colors.HexColor("#37474f"))

    story: list = []
    story.extend(_build_header(_escape(student_name), report.get("generated_at", ""), styles, subtitle="Relatório do Kanban"))
    teacher = filters.get("teacher_name") or "Todos"
    story.append(Paragraph(f"<b>Professor responsável:</b> {_escape(teacher)}", small))
    story.append(Paragraph(_escape(_filters_text(filters)), muted))
    story.append(Spacer(1, 6))

    counts = report.get("counts", {})
    shown = [s for s in STATUS_LABELS if s in (filters.get("statuses") or STATUS_LABELS)]
    t = Table([[STATUS_LABELS[s] for s in shown], [str(counts.get(s, 0)) for s in shown]], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    page_w = A4[0] - 3.6 * cm
    date_w = 2.2 * cm if include_dates else 0
    resp_w = 3.4 * cm
    widths = [page_w - resp_w - date_w, resp_w] + ([date_w] if include_dates else [])

    columns = report.get("columns", {})
    any_card = False
    for status in shown:
        cards = columns.get(status, [])
        if not cards:
            continue
        any_card = True
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"{STATUS_LABELS[status]} ({len(cards)})", styles["h1"]))
        head = [Paragraph("Ação", small_b), Paragraph("Professor responsável", small_b)]
        if include_dates:
            head.append(Paragraph("Atualizado", small_b))
        rows, style = [head], [
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.3, GRID),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        last_skill = None
        ncols = len(head)
        if not include_actions:  # só o resumo: quantas ações há em cada habilidade desta coluna
            tally: dict[str, int] = {}
            for c in cards:
                tally[_skill_title(c)] = tally.get(_skill_title(c), 0) + 1
            rows = [[Paragraph("Habilidade", small_b), Paragraph("Ações", small_b)]]
            rows += [[Paragraph(_escape(k), small), Paragraph(str(v), small)] for k, v in tally.items()]
            tbl = Table(rows, colWidths=[page_w - 2 * cm, 2 * cm], repeatRows=1)
            tbl.setStyle(TableStyle(style))
            story.append(tbl)
            continue
        for c in cards:
            key = (c.get("skill_code"), c.get("skill_grade"), c.get("skill_area"))
            if key != last_skill:  # cabeçalho da habilidade, ocupando a linha toda
                last_skill = key
                rows.append([Paragraph(_escape(_skill_title(c)), small_b)] + [""] * (ncols - 1))
                r = len(rows) - 1
                style += [("SPAN", (0, r), (-1, r)), ("BACKGROUND", (0, r), (-1, r), colors.HexColor("#eef1f8"))]
            row = [Paragraph(_escape(c["title"]), small), Paragraph(_escape(c.get("responsible_name") or ""), small)]
            if include_dates:
                row.append(Paragraph(_fmt_date(c.get("updated_at")), small))
            rows.append(row)
            entries = c.get("entries", []) if include_entries else []
            if entries:
                lines = []
                for e in entries:
                    reaction = f" — reação {e['reaction']}/5" if e.get("reaction") else ""
                    when = f"<b>{_fmt_date(e['entry_date'])}</b>: " if include_dates else ""
                    lines.append(Paragraph(f"{when}{_escape(e.get('text') or '')}{reaction}", entry_style))
                rows.append([[Paragraph("Diário da ação", muted)] + lines] + [""] * (ncols - 1))
                r = len(rows) - 1
                style += [("SPAN", (0, r), (-1, r)), ("BACKGROUND", (0, r), (-1, r), colors.HexColor("#fafafa"))]
        tbl = Table(rows, colWidths=widths, repeatRows=1)
        tbl.setStyle(TableStyle(style))
        story.append(tbl)

    if not any_card:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Nenhuma ação corresponde aos filtros escolhidos.", styles["body"]))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRID, spaceAfter=6))
    story.append(Paragraph("Documento gerado pelo sistema Autism.iA.", styles["confidential"]))
    doc.build(story, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
    return buf.getvalue()
