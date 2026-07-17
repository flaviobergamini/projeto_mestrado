"""PDF generation service for PEI documents using ReportLab."""

import io
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Brand colors ──────────────────────────────────────────────────────────────
PRIMARY = colors.HexColor("#1a237e")   # deep blue
ACCENT  = colors.HexColor("#1565c0")  # medium blue
LIGHT   = colors.HexColor("#e8eaf6")  # lavender tint
TEXT    = colors.HexColor("#212121")
MUTED   = colors.HexColor("#757575")

# ── Logo path (try backend assets, then frontend public) ──────────────────────
_BACKEND_ROOT = Path(__file__).parent.parent.parent
_LOGO_CANDIDATES = [
    _BACKEND_ROOT / "assets" / "autismia_logo.png",
    _BACKEND_ROOT.parent / "agents-frontend" / "public" / "icons" / "icon-192.png",
]
LOGO_PATH: Optional[str] = next((str(p) for p in _LOGO_CANDIDATES if p.exists()), None)


# ── Styles ─────────────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "h1": s("H1", fontName="Helvetica-Bold", fontSize=16, textColor=PRIMARY,
                 spaceAfter=6, spaceBefore=12, alignment=TA_LEFT),
        "h2": s("H2", fontName="Helvetica-Bold", fontSize=13, textColor=ACCENT,
                 spaceAfter=4, spaceBefore=10, alignment=TA_LEFT),
        "h3": s("H3", fontName="Helvetica-Bold", fontSize=11, textColor=TEXT,
                 spaceAfter=3, spaceBefore=8, alignment=TA_LEFT),
        "body": s("Body", fontName="Helvetica", fontSize=10, textColor=TEXT,
                  spaceAfter=4, leading=14, alignment=TA_JUSTIFY),
        "bullet": s("Bullet", fontName="Helvetica", fontSize=10, textColor=TEXT,
                    spaceAfter=2, leading=13, leftIndent=14, bulletIndent=4),
        "caption": s("Caption", fontName="Helvetica-Oblique", fontSize=8,
                     textColor=MUTED, alignment=TA_CENTER),
        "header_name": s("HdrName", fontName="Helvetica-Bold", fontSize=18,
                         textColor=PRIMARY, alignment=TA_LEFT),
        "header_sub": s("HdrSub", fontName="Helvetica", fontSize=9,
                        textColor=MUTED, alignment=TA_LEFT),
        "info_label": s("InfoLabel", fontName="Helvetica-Bold", fontSize=9,
                        textColor=MUTED),
        "info_value": s("InfoValue", fontName="Helvetica", fontSize=10,
                        textColor=TEXT),
        "confidential": s("Confidential", fontName="Helvetica-Oblique", fontSize=8,
                          textColor=MUTED, alignment=TA_CENTER),
    }


# ── Markdown → ReportLab flowables ─────────────────────────────────────────────

def _escape(text: str) -> str:
    """Escape XML special chars for ReportLab paragraphs."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(text: str) -> str:
    """Convert **bold** and *italic* to ReportLab tags."""
    text = _escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text


def _parse_markdown(text: str, styles: dict) -> list:
    """Parse markdown-like PEI text into a list of ReportLab flowables."""
    flowables = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not line.strip():
            flowables.append(Spacer(1, 3))
            i += 1
            continue

        # Headings
        if line.startswith("### "):
            flowables.append(Paragraph(_inline(line[4:]), styles["h3"]))
        elif line.startswith("## "):
            flowables.append(Paragraph(_inline(line[3:]), styles["h2"]))
        elif line.startswith("# "):
            flowables.append(Paragraph(_inline(line[2:]), styles["h1"]))

        # Bullets
        elif re.match(r"^[-*•]\s+", line):
            content = re.sub(r"^[-*•]\s+", "", line)
            flowables.append(Paragraph(f"• {_inline(content)}", styles["bullet"]))

        # Numbered list
        elif re.match(r"^\d+\.\s+", line):
            content = re.sub(r"^\d+\.\s+", "", line)
            num = re.match(r"^(\d+)\.", line).group(1)
            flowables.append(Paragraph(f"{num}. {_inline(content)}", styles["bullet"]))

        # Horizontal rule
        elif line.strip() in ("---", "***", "___"):
            flowables.append(HRFlowable(width="100%", thickness=0.5,
                                        color=colors.HexColor("#bdbdbd"), spaceAfter=6))

        # Regular paragraph
        else:
            flowables.append(Paragraph(_inline(line), styles["body"]))

        i += 1

    return flowables


# ── Header builder ──────────────────────────────────────────────────────────────

_BRT = timezone(timedelta(hours=-3))


def _build_header(student_name: str, generated_at: str, styles: dict) -> list:
    """Return flowables for the letterhead header."""
    elements = []

    # Logo (optional)
    logo_img = None
    if LOGO_PATH:
        try:
            logo_img = Image(LOGO_PATH, width=2.0 * cm, height=2.0 * cm)
        except Exception:
            pass

    # Title block: single Paragraph with inline tags so it sits in one cell,
    # avoiding the overlap that happens when a list of flowables shares a row.
    title_para = Paragraph(
        'Autism.iA<br/>'
        '<font size="9" color="#757575">'
        'Sistema de Geração de Planos Educacionais Individualizados via IA<br/>'
        'Plano Educacional Individualizado — PEI'
        '</font>',
        styles["header_name"],
    )

    if logo_img:
        header_table = Table(
            [[logo_img, title_para]],
            colWidths=[2.6 * cm, None],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
    else:
        elements.append(title_para)

    elements.append(Spacer(1, 6))
    elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=10))

    # Student info box — horário em Brasília (UTC-3)
    try:
        raw = generated_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt_brt = dt.astimezone(_BRT)
        date_str = dt_brt.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        date_str = generated_at

    info_data = [
        [Paragraph("<b>Aluno(a):</b>", styles["info_label"]),
         Paragraph(student_name, styles["info_value"]),
         Paragraph("<b>Gerado em:</b>", styles["info_label"]),
         Paragraph(date_str, styles["info_value"])],
    ]
    info_table = Table(info_data, colWidths=[2.8 * cm, None, 2.5 * cm, 4 * cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 12))

    return elements


# ── Footer ──────────────────────────────────────────────────────────────────────

def _footer_canvas(canvas, doc):
    canvas.saveState()
    width, height = A4
    # Bottom rule
    canvas.setStrokeColor(colors.HexColor("#bdbdbd"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 1.8 * cm, width - doc.rightMargin, 1.8 * cm)
    # Footer text
    canvas.setFont("Helvetica-Oblique", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 1.4 * cm,
                      "Documento confidencial gerado pelo sistema Autism.iA — uso restrito à equipe pedagógica.")
    canvas.drawRightString(width - doc.rightMargin, 1.4 * cm, f"Página {doc.page}")
    canvas.restoreState()


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_pei_pdf(
    pei_text: str,
    student_name: str,
    generated_at: str,
) -> bytes:
    """Generate a letterhead PDF for the given PEI and return raw bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.8 * cm,
        title=f"PEI — {student_name}",
        author="Autism.iA",
        subject="Plano Educacional Individualizado",
    )

    styles = _build_styles()
    story: list = []

    # Header
    story.extend(_build_header(student_name, generated_at, styles))

    # PEI content
    story.extend(_parse_markdown(pei_text, styles))

    # Footer notice at end of content
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#bdbdbd"), spaceAfter=6))
    story.append(Paragraph(
        "Este documento foi gerado automaticamente pelo sistema Autism.iA com base em dados "
        "anonimizados do aluno. Deve ser revisado por profissionais habilitados antes de ser "
        "implementado.",
        styles["confidential"],
    ))

    doc.build(story, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
    return buf.getvalue()


def generate_chat_pdf(messages: list[dict], title: str = "Chat") -> bytes:
    """Generate a PDF export of a chat session."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
    )
    styles = _build_styles()
    br_tz = timezone(timedelta(hours=-3))
    generated_at = datetime.now(br_tz).strftime("%d/%m/%Y %H:%M")


    story: list = []

    # ── Header ────────────────────────────────────────────────────────────────
    if LOGO_PATH:
        story.append(Image(LOGO_PATH, width=2 * cm, height=2 * cm))
        story.append(Spacer(1, 4))

    story.append(Paragraph("Autism.iA — Exportação de Chat", styles["h1"]))
    story.append(Paragraph(title, styles["h2"]))
    story.append(Paragraph(f"Gerado em: {generated_at}", styles["caption"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=10))

    if not messages:
        story.append(Paragraph("Nenhuma mensagem nesta sessão.", styles["body"]))
    else:
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            ts = msg.get("created_at", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    ts = dt.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    pass

            if role == "user":
                label = "<font color='#1a237e'>Você</font>"
            else:
                label = "<font color='#1565c0'>Autism.iA</font>"

            header_text = f"<b>{label}</b>  <font size='8' color='#9e9e9e'>{ts}</font>"
            header_para = Paragraph(header_text, styles["body"])

            lines = content.split("\n")
            body_paras = [Paragraph(ln if ln.strip() else "&nbsp;", styles["body"]) for ln in lines]

            block = KeepTogether([header_para, Spacer(1, 2)] + body_paras + [Spacer(1, 8)])
            story.append(block)

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#bdbdbd"), spaceAfter=6))
    story.append(Paragraph(
        "Documento gerado automaticamente pelo sistema Autism.iA.",
        styles["confidential"],
    ))

    doc.build(story, onFirstPage=_footer_canvas, onLaterPages=_footer_canvas)
    return buf.getvalue()
