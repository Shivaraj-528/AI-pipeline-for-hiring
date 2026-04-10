"""
convert_report.py
Converts NOVARA_REPORT.md to a formatted PDF using reportlab.
Run: python3 convert_report.py
"""

import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ── Paths ──────────────────────────────────────
MD_FILE  = Path("NOVARA_REPORT.md")
PDF_FILE = Path("NOVARA_REPORT.pdf")

# ── Color Palette ──────────────────────────────
DARK_BG      = colors.HexColor("#0d1117")
ACCENT_BLUE  = colors.HexColor("#1f6feb")
ACCENT_TEAL  = colors.HexColor("#238636")
HEADING_COLOR = colors.HexColor("#1a237e")
SUBHEAD_COLOR = colors.HexColor("#0277bd")
CODE_BG      = colors.HexColor("#f6f8fa")
CODE_FG      = colors.HexColor("#24292f")
TABLE_HEADER  = colors.HexColor("#1a237e")
TABLE_ROW_ALT = colors.HexColor("#e8eaf6")
TEXT_COLOR   = colors.HexColor("#24292f")
RULE_COLOR   = colors.HexColor("#1f6feb")

# ── Styles ─────────────────────────────────────
def make_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "DocTitle",
        fontSize=26, textColor=HEADING_COLOR,
        spaceAfter=6, spaceBefore=10,
        alignment=TA_CENTER, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        "DocSubtitle",
        fontSize=13, textColor=SUBHEAD_COLOR,
        spaceAfter=4, spaceBefore=2,
        alignment=TA_CENTER, fontName="Helvetica"
    ))
    styles.add(ParagraphStyle(
        "H1",
        fontSize=18, textColor=HEADING_COLOR,
        spaceAfter=6, spaceBefore=14,
        fontName="Helvetica-Bold", borderPad=4
    ))
    styles.add(ParagraphStyle(
        "H2",
        fontSize=14, textColor=SUBHEAD_COLOR,
        spaceAfter=4, spaceBefore=10,
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        "H3",
        fontSize=12, textColor=SUBHEAD_COLOR,
        spaceAfter=3, spaceBefore=8,
        fontName="Helvetica-BoldOblique"
    ))
    styles.add(ParagraphStyle(
        "BodyText2",
        fontSize=10, textColor=TEXT_COLOR,
        spaceAfter=3, spaceBefore=1,
        leading=15, alignment=TA_JUSTIFY,
        fontName="Helvetica"
    ))
    styles.add(ParagraphStyle(
        "BulletText",
        fontSize=10, textColor=TEXT_COLOR,
        spaceAfter=2, spaceBefore=1,
        leftIndent=16, leading=14,
        fontName="Helvetica", bulletIndent=6
    ))
    styles.add(ParagraphStyle(
        "CodeText",
        fontSize=8.5, textColor=CODE_FG,
        spaceAfter=2, spaceBefore=2,
        leftIndent=10, fontName="Courier",
        backColor=CODE_BG, leading=13
    ))
    styles.add(ParagraphStyle(
        "Blockquote",
        fontSize=10, textColor=SUBHEAD_COLOR,
        spaceAfter=4, spaceBefore=4,
        leftIndent=18, fontName="Helvetica-Oblique",
        leading=14
    ))
    return styles

# ── Helpers ────────────────────────────────────
def clean(text):
    """Strip markdown formatting for plain paragraph use."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)   # bold
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>",  text)   # italic
    text = re.sub(r"`(.+?)`",       r"<font name='Courier'>\1</font>", text)  # inline code
    text = re.sub(r"^#+\s*",        "",              text)   # strip # chars
    text = re.sub(r"^[-*]\s+",      "• ",            text)   # bullets
    return text.strip()

def parse_table(lines):
    """Parse markdown table lines into list-of-lists."""
    rows = []
    for line in lines:
        if re.match(r"^\s*\|[-: |]+\|\s*$", line):
            continue  # separator row
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows

def build_pdf_table(rows, styles):
    if not rows:
        return None

    header = rows[0]
    data   = rows[1:] if len(rows) > 1 else []

    # Style header cells
    header_cells = [Paragraph(f"<b>{c}</b>", ParagraphStyle(
        "TH", fontSize=9, textColor=colors.white,
        fontName="Helvetica-Bold", alignment=TA_CENTER, leading=12
    )) for c in header]

    # Style data cells
    table_data = [header_cells]
    for ri, row in enumerate(data):
        cells = []
        for ci, cell in enumerate(row):
            cleaned = clean(cell).replace("✅", "Y").replace("❌", "N").replace("•", "")
            style = ParagraphStyle(
                "TD", fontSize=8.5, textColor=TEXT_COLOR,
                fontName="Helvetica", leading=12,
                alignment=TA_CENTER if ci > 0 else TA_LEFT
            )
            cells.append(Paragraph(cleaned, style))
        table_data.append(cells)

    col_count = len(header)
    page_width = A4[0] - 4*cm
    col_w = page_width / col_count

    t = Table(table_data, colWidths=[col_w]*col_count, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  TABLE_HEADER),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d0d0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TABLE_ROW_ALT]),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t

# ── Main Converter ──────────────────────────────
def convert():
    styles = make_styles()
    story  = []
    md_text = MD_FILE.read_text(encoding="utf-8")
    lines   = md_text.splitlines()

    i = 0
    in_code_block   = False
    in_table_block  = False
    table_lines     = []
    code_lines      = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Code block ──
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                if code_lines:
                    for cl in code_lines:
                        safe = cl.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        story.append(Paragraph(safe or " ", styles["CodeText"]))
                story.append(Spacer(1, 4))
                in_code_block = False
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # ── Table detection ──
        if stripped.startswith("|"):
            table_lines.append(stripped)
            i += 1
            continue
        else:
            if table_lines:
                pdf_table = build_pdf_table(parse_table(table_lines), styles)
                if pdf_table:
                    story.append(Spacer(1, 6))
                    story.append(pdf_table)
                    story.append(Spacer(1, 8))
                table_lines = []

        # ── Horizontal rules ──
        if stripped in ("---", "===", "───"):
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=1.2, color=RULE_COLOR))
            story.append(Spacer(1, 6))
            i += 1
            continue

        # ── Blank line ──
        if not stripped:
            story.append(Spacer(1, 4))
            i += 1
            continue

        # ── Headings ──
        if stripped.startswith("# ") and not stripped.startswith("## "):
            story.append(Spacer(1, 8))
            story.append(Paragraph(clean(stripped[2:]), styles["H1"]))
            story.append(HRFlowable(width="100%", thickness=0.8, color=RULE_COLOR))
            story.append(Spacer(1, 4))
            i += 1
            continue

        if stripped.startswith("## "):
            story.append(Spacer(1, 6))
            story.append(Paragraph(clean(stripped[3:]), styles["H2"]))
            i += 1
            continue

        if stripped.startswith("### "):
            story.append(Paragraph(clean(stripped[4:]), styles["H3"]))
            i += 1
            continue

        if stripped.startswith("#### "):
            story.append(Paragraph(f"<b>{clean(stripped[5:])}</b>", styles["BodyText2"]))
            i += 1
            continue

        # ── Blockquote ──
        if stripped.startswith(">"):
            story.append(Paragraph(clean(stripped[1:].strip()), styles["Blockquote"]))
            i += 1
            continue

        # ── Bullet ──
        if re.match(r"^[-*•]\s+", stripped):
            text = re.sub(r"^[-*•]\s+", "", stripped)
            story.append(Paragraph("• " + clean(text), styles["BulletText"]))
            i += 1
            continue

        # ── Numbered list ──
        if re.match(r"^\d+\.\s+", stripped):
            text = re.sub(r"^\d+\.\s+", "", stripped)
            story.append(Paragraph("• " + clean(text), styles["BulletText"]))
            i += 1
            continue

        # ── Normal paragraph ──
        if stripped:
            story.append(Paragraph(clean(stripped), styles["BodyText2"]))
            i += 1
            continue

        i += 1

    # flush any remaining table
    if table_lines:
        pdf_table = build_pdf_table(parse_table(table_lines), styles)
        if pdf_table:
            story.append(pdf_table)

    # ── Build PDF ──
    doc = SimpleDocTemplate(
        str(PDF_FILE),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2.2*cm,
        bottomMargin=2*cm,
        title="AgentForge — Novara Hackathon Report",
        author="Shivaraj Yelugodla",
        subject="AI-Powered Autonomous Technical Recruitment System"
    )

    def on_page(canvas, doc):
        canvas.saveState()
        # Header bar
        canvas.setFillColor(HEADING_COLOR)
        canvas.rect(0, A4[1]-1*cm, A4[0], 1*cm, fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(colors.white)
        canvas.drawString(2*cm, A4[1]-0.65*cm, "AgentForge — Novara Hackathon 2026")
        canvas.drawRightString(A4[0]-2*cm, A4[1]-0.65*cm, "Team Antariksh | Shivaraj Yelugodla")
        # Footer
        canvas.setFillColor(colors.HexColor("#444444"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(2*cm, 0.6*cm, "Confidential — Novara Hackathon 2026")
        canvas.drawRightString(A4[0]-2*cm, 0.6*cm, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"✅ PDF created: {PDF_FILE.resolve()}")

if __name__ == "__main__":
    convert()
