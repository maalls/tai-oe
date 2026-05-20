# LLM Vision Extractor

## Objectif

Mutualiser l'extraction de donnees structurees depuis des PDF via un LLM compatible vision.

Le module central est `src/lib/llm_vision_extractor.py` avec la fonction:

- `extract_from_pdf_with_vision(pdf_path, llm_client, system_prompt, user_prompt, ...)`

## Fonctionnement

1. Rend chaque page PDF en image (via `pypdfium2`).
2. Encode les images en data URLs base64.
3. Construit un prompt chat vision:
   - role `system`: prompt metier global
   - role `user`: bloc texte + blocs `image_url`
4. Appelle le LLM vision et recupere le contenu.
5. Parse la reponse JSON (avec fallback robuste).

## Parametres principaux

- `pdf_path`: chemin du PDF d'entree.
- `llm_client`: client LLM OpenAI-compatible (doit exposer `client` et `model`).
- `system_prompt`: consignes systeme metier.
- `user_prompt`: consignes utilisateur metier.
- `temperature`, `max_tokens`: options de generation.
- `image_scale`, `image_format`, `image_quality`: qualite des pages rendues.
- `json_response`: active `response_format={"type": "json_object"}` avec fallback auto.

## Usages actuels

- Discounts: `src/lib/importers/discount.py`
- Quotes/RFP PDF (mode vision): `src/lib/extractors/text_reader.py` + `src/service/opportunity/document_rfp_extraction_service.py`

## Flags d'environnement

- `QUOTE_EXTRACTION_MODE=text|vision`
- `DISCOUNT_EXTRACTION_MODE=text|vision`

Valeurs recommandees:

- Quote: `text` en production prudente, `vision` si le modele VL est stable.
- Discount: `vision` par defaut (historique du flux).

## Ajouter un nouveau cas metier

1. Definir un prompt systeme et un prompt utilisateur metier.
2. Appeler `extract_from_pdf_with_vision(...)` dans le service/importer cible.
3. Normaliser le JSON de sortie dans une fonction metier dediee.
4. Ajouter un flag `*_EXTRACTION_MODE=text|vision` si le flux doit rester pilotable.
5. Ajouter:
   - un test unitaire de parsing metier
   - un test de selection de mode (`text` vs `vision`)
   - un test d'integration du flux cible

## Exemple minimal

```python
from src.lib.llm_vision_extractor import extract_from_pdf_with_vision

parsed = extract_from_pdf_with_vision(
    pdf_path,
    llm_client,
    system_prompt="You extract product rows. Return JSON only.",
    user_prompt="Extract RFQ product lines from this document.",
    max_tokens=1200,
)
products = parsed.get("products", [])
```

## Limites connues

- Cout/latence plus eleves qu'un flux texte.
- Qualite dependante de la lisibilite visuelle du PDF.
- Requiert un modele LLM vraiment compatible vision.
