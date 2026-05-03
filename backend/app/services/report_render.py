import csv
import io
from collections.abc import Iterator
from typing import Any
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Paisagem = mais largura para muitas colunas; margens explícitas evitam corte nas bordas.
_PAGE = landscape(letter)
_MARGIN = 0.45 * inch


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def iter_csv_rows(rows: list[dict[str, object]], headers: list[str]) -> Iterator[bytes]:
    """Stream CSV as UTF-8 chunks (header + one chunk per data row)."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    yield buffer.getvalue().encode("utf-8")
    buffer.seek(0)
    buffer.truncate(0)
    for row in rows:
        writer.writerow({h: _cell(row.get(h)) for h in headers})
        yield buffer.getvalue().encode("utf-8")
        buffer.seek(0)
        buffer.truncate(0)


def chart_bar(labels: list[str], values: list[float], title: str) -> bytes:
    """Render a simple bar chart as PNG bytes (larga para caber no PDF paisagem)."""
    safe_labels = [lbl[:40] + "…" if len(lbl) > 40 else lbl for lbl in labels]
    fig, ax = plt.subplots(figsize=(10, 3.4))
    x = range(len(safe_labels))
    ax.bar(x, values, color="#2563eb")
    ax.set_xticks(list(x))
    ax.set_xticklabels(safe_labels, rotation=32, ha="right", fontsize=7)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel("Valor")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def to_pdf(
    title: str,
    subtitle: str,
    rows: list[dict[str, object]],
    headers: list[str],
    chart_png: bytes | None = None,
) -> bytes:
    """PDF em modo paisagem, tabela com colunas proporcionais e texto quebrando linha."""
    buf = io.BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        buf,
        pagesize=_PAGE,
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )

    usable_width = _PAGE[0] - doc.leftMargin - doc.rightMargin

    cell_style = ParagraphStyle(
        name="tbl_cell",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        alignment=TA_LEFT,
    )
    hdr_cell_style = ParagraphStyle(
        name="tbl_hdr",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        alignment=TA_LEFT,
        textColor=colors.whitesmoke,
    )

    story: list[Any] = []
    story.append(Paragraph(f"<b>{escape(title)}</b>", styles["Title"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph(escape(subtitle), styles["Normal"]))
    story.append(Spacer(1, 0.16 * inch))

    if chart_png:
        img_w = min(usable_width, 9.2 * inch)
        img_h = 2.85 * inch
        img = RLImage(io.BytesIO(chart_png), width=img_w, height=img_h)
        story.append(img)
        story.append(Spacer(1, 0.2 * inch))

    if not rows:
        story.append(Paragraph("<i>Nenhuma linha neste período.</i>", styles["Normal"]))
        doc.build(story)
        buf.seek(0)
        return buf.getvalue()

    n = len(headers)
    col_w = usable_width / n
    col_widths = [col_w] * n

    header_row = [Paragraph(f"<b>{escape(str(h))}</b>", hdr_cell_style) for h in headers]
    table_data: list[list[Any]] = [header_row]
    for row in rows:
        table_data.append(
            [Paragraph(escape(_cell(row.get(h))), cell_style) for h in headers]
        )

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(tbl)
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
