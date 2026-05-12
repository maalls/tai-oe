#!/usr/bin/env python3
"""List random product references from Postgres."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACK_DIR = SCRIPT_DIR.parent
SRC_DIR = BACK_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from controller.db_client import DatabaseHandler  # noqa: E402

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import mm, inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def _build_query() -> str:
    return """
        SELECT
            marque,
            refciale AS reference,
            COALESCE(libelle240, libelle80, libelle40, refinfor, fonction) AS description
        FROM fabdis_commerce
        WHERE COALESCE(libelle240, libelle80, libelle40, refinfor, fonction) IS NOT NULL
        ORDER BY random()
        LIMIT %s
    """


def _get_table_data(rows: list[dict], min_qty: int, max_qty: int) -> list[list[str]]:
    """Extract table data as list of lists."""
    data = [["marque", "refciale", "Description", "Quantity"]]
    for row in rows:
        qty = random.randint(min_qty, max_qty)
        marque = str(row.get("marque", "")).strip()
        reference = str(row.get("reference", "")).strip()
        description = str(row.get("description", "")).strip()
        data.append([marque, reference, description, str(qty)])
    return data


def _as_markdown(rows: list[dict], min_qty: int, max_qty: int) -> str:
    lines = ["| marque | refciale | Description | Quantity |", "|---|---|---|---:|"]
    for row in rows:
        qty = random.randint(min_qty, max_qty)
        marque = str(row.get("marque", "")).strip()
        reference = str(row.get("reference", "")).strip()
        description = str(row.get("description", "")).strip()
        lines.append(f"| {marque} | {reference} | {description} | {qty} |")
    return "\n".join(lines)


def _as_pdf(rows: list[dict], min_qty: int, max_qty: int, output_path: str | None = None) -> str:
    """Generate PDF from product data as a quote request."""
    if not REPORTLAB_AVAILABLE:
        raise SystemExit("reportlab is required for PDF output. Install with: pip install reportlab")
    
    from reportlab.lib.units import mm, inch
    from reportlab.platypus import Spacer, Paragraph
    
    output_file = output_path or "products.pdf"
    
    # Create PDF document with margins
    doc = SimpleDocTemplate(
        output_file, 
        pagesize=A4, 
        topMargin=15*mm, 
        bottomMargin=15*mm,
        leftMargin=15*mm,
        rightMargin=15*mm
    )
    story = []
    styles = getSampleStyleSheet()
    
    # Company header
    company_style = styles['Normal']
    company_style.fontSize = 12
    company_style.leading = 14
    
    header_lines = [
        "<b>ÉLECTRICALS DISTRIBUTION FRANCE SAS</b>",
        "123, Avenue de l'Industrie",
        "78400 Chatou, France",
        "Tél: +33 (0)1 23 45 67 89",
        "Email: contact@edistribution.fr",
    ]
    
    for line in header_lines:
        story.append(Paragraph(line, company_style))
    
    # Add spacing
    story.append(Spacer(1, 0.3*inch))
    
    # Title
    title_style = styles['Heading1']
    title_style.fontSize = 16
    title_style.textColor = colors.HexColor('#003366')
    title_style.spaceAfter = 12
    title = Paragraph("DEMANDE DE DEVIS", title_style)
    story.append(title)
    
    # Add spacing
    story.append(Spacer(1, 0.2*inch))
    
    # Prepare table data with cropped descriptions
    data = [["Marque", "Référence", "Description", "Quantité"]]
    for row in rows:
        qty = random.randint(min_qty, max_qty)
        marque = str(row.get("marque", "")).strip()
        reference = str(row.get("reference", "")).strip()
        description = str(row.get("description", "")).strip()
        
        # Crop description to reasonable length for PDF
        if len(description) > 60:
            description = description[:60] + "..."
        
        data.append([marque, reference, description, str(qty)])
    
    # Create table with data
    col_widths = [50*mm, 50*mm, 80*mm, 25*mm]
    table = Table(data, colWidths=col_widths)
    
    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    story.append(table)
    
    # Add footer with date and signature area
    story.append(Spacer(1, 0.3*inch))
    
    footer_style = styles['Normal']
    footer_style.fontSize = 9
    footer_style.leading = 12
    
    date_line = Paragraph(f"<b>Date:</b> {__import__('datetime').datetime.now().strftime('%d/%m/%Y')}", footer_style)
    story.append(date_line)
    
    story.append(Spacer(1, 0.2*inch))
    signature = Paragraph("<b>Signature:</b> _" + "_" * 40, footer_style)
    story.append(signature)
    
    # Build PDF
    doc.build(story)
    return output_file


def main() -> int:
    parser = argparse.ArgumentParser(description="List random product references.")
    parser.add_argument("--count", type=int, default=10, help="Number of products to list")
    parser.add_argument("--min-qty", type=int, default=1, help="Minimum random quantity")
    parser.add_argument("--max-qty", type=int, default=100, help="Maximum random quantity")
    parser.add_argument("--format", choices=["markdown", "pdf"], default="markdown", help="Output format (markdown or pdf)")
    parser.add_argument("--output", type=str, default=None, help="Output file path (for PDF format)")
    args = parser.parse_args()

    if args.count <= 0:
        raise SystemExit("--count must be > 0")
    if args.min_qty <= 0 or args.max_qty <= 0 or args.min_qty > args.max_qty:
        raise SystemExit("Invalid quantity bounds")

    db_handler = DatabaseHandler()
    rows = db_handler.execute_dict_query(_build_query(), (args.count,))

    if args.format == "pdf":
        output_file = _as_pdf(rows, args.min_qty, args.max_qty, args.output)
        print(f"PDF generated: {output_file}")
    else:
        print(_as_markdown(rows, args.min_qty, args.max_qty))
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
