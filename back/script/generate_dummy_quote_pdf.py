#!/usr/bin/env python3
"""Generate a dummy RFQ PDF from a predefined product list."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from weasyprint import HTML


def build_html(items: list[dict]) -> str:
    issued_date = datetime.now().strftime("%Y-%m-%d")
    rfq_id = f"RFQ-{datetime.now().strftime('%Y%m%d')}-001"

    company = {
        "name": "Acme Electric Supply",
        "address": "123 Market Street",
        "city": "Paris",
        "postal_code": "75001",
        "country": "France",
        "phone": "+33 1 23 45 67 89",
        "email": "sales@acme-electric.example",
    }

    requester = {
        "name": "Malo Milki Yamakado",
        "address": "45 Rue de la Paix",
        "city": "Paris",
        "postal_code": "75002",
        "country": "France",
        "email": "purchasing@example.com",
    }

    rows = "\n".join(
        f"""
        <tr>
            <td>{item['refciale']}</td>
            <td>{item['description']}</td>
            <td class="qty">{item['quantity']}</td>
        </tr>
        """.strip()
        for item in items
    )

    return f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Request for Quote</title>
    <style>
      @page {{ margin: 36px; }}
      body {{ font-family: Arial, sans-serif; color: #111; }}
      h1 {{ font-size: 22px; margin: 0 0 8px; }}
      h2 {{ font-size: 16px; margin: 0 0 12px; }}
      .meta {{ font-size: 12px; color: #444; }}
      .header {{ display: flex; justify-content: space-between; margin-bottom: 24px; }}
      .block {{ font-size: 12px; line-height: 1.5; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
      th, td {{ border: 1px solid #333; padding: 8px; font-size: 12px; }}
      th {{ background: #f0f0f0; text-align: left; }}
      .qty {{ text-align: right; width: 80px; }}
    </style>
  </head>
  <body>
    <div class="header">
      <div>
        <h1>Request for Quote</h1>
        <div class="meta">RFQ: {rfq_id}</div>
        <div class="meta">Date: {issued_date}</div>
      </div>
      <div class="block">
        <strong>{company['name']}</strong><br />
        {company['address']}<br />
        {company['postal_code']} {company['city']}, {company['country']}<br />
        {company['phone']}<br />
        {company['email']}
      </div>
    </div>

    <div class="block">
      <strong>Requested By:</strong><br />
      {requester['name']}<br />
      {requester['address']}<br />
      {requester['postal_code']} {requester['city']}, {requester['country']}<br />
      {requester['email']}
    </div>

    <h2>Requested Items</h2>
    <table>
      <thead>
        <tr>
          <th>Refciale</th>
          <th>Description</th>
          <th class="qty">Quantity</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </body>
</html>
""".strip()


def main() -> int:
    items = [
        {
            "refciale": "PVDE2440",
            "description": "Kit Vert. E2.2/E4.2 3/4P Debro Chariot Int. H=600mm L=800mm",
            "quantity": 95,
        },
        {
            "refciale": "922416",
            "description": "Fusible Couteau 355A AM Taille 2 690V",
            "quantity": 39,
        },
        {
            "refciale": "352490",
            "description": "Disjoncteur Modulaire Tertiaire/Indus. - Serie S200 - 4P - 230V/400VAC -25A - Courbe K - Icn 6000A / Icu 10kA",
            "quantity": 9,
        },
        {
            "refciale": "PPFI4728",
            "description": "Plastron Mesure 4 72X72 L=800mm (x1)",
            "quantity": 28,
        },
        {
            "refciale": "200055",
            "description": "Fin de Course Ls31P31B11",
            "quantity": 21,
        },
        {
            "refciale": "HV040262",
            "description": "Bouton-poussoir a usage industriel Rouge 1NO 1Nc",
            "quantity": 14,
        },
        {
            "refciale": "BJE93577",
            "description": "Futur Linear / Enjoliveur pour detecteur de mouvement - Blanc Mat",
            "quantity": 39,
        },
        {
            "refciale": "F711944",
            "description": "Coffret de distribution avec porte transparente - Saillie - 2 rangees, 2x12 modules",
            "quantity": 35,
        },
        {
            "refciale": "B752549",
            "description": "Parafoudre OVR T2 3L 80-275S P QS",
            "quantity": 53,
        },
        {
            "refciale": "PKOH3160",
            "description": "Kit Horiz. Ot 315/400 3/4P Fixe H=300mm L=600mm",
            "quantity": 82,
        },
    ]

    output_path = Path("external/rag/quote.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html_content = build_html(items)
    HTML(string=html_content).write_pdf(str(output_path))
    print(f"PDF generated at {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
