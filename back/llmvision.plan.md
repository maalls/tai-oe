# Refactorisation extraction PDF via LLM Vision

## Objectif

Unifier la logique d'extraction de données métier (devis, discounts, etc.) depuis des PDF via LLM vision pour éviter la duplication de code (conversion PDF → images, prompt vision, appel LLM, parsing).

## Plan d'exécution

### 1. Analyse des usages actuels

- Identifier tous les endroits où l'on extrait des données métier depuis un PDF via LLM vision (discounts, devis, etc.).
- Repérer les points communs : conversion PDF en images, encodage base64, construction du prompt vision, appel LLM, parsing du résultat.

### 2. Définir une API/fonction générique

- Créer un module utilitaire (ex: `lib/llm_vision_extractor.py`).
- Fonction principale : `extract_from_pdf_with_vision(pdf_path, system_prompt, user_prompt, llm_client, **kwargs)`
  - Convertit chaque page du PDF en image (JPEG, base64)
  - Construit le prompt vision (system + user + images)
  - Appelle le LLM vision
  - Retourne le résultat brut ou parsé
- Permettre de passer des prompts métier différents selon le contexte (devis, discounts, etc.)

### 3. Refactoriser les usages métier

- Dans chaque module métier (discount, devis, etc.) :
  - Remplacer la logique vision spécifique par un appel à la fonction générique
  - Fournir le prompt métier adapté
  - Gérer le parsing métier du résultat si besoin

### 4. Gestion du mode extraction

- Centraliser la gestion du flag `.env` (QUOTE_EXTRACTION_MODE, DISCOUNT_EXTRACTION_MODE, etc.)
- Sélectionner la fonction d'extraction (texte ou vision) selon le flag

### 5. Tests & validation

- Ajouter des tests unitaires pour la fonction générique (cas PDF multi-pages, erreurs, etc.)
- Tester chaque usage métier refactoré (discount, devis)

### 6. Documentation

- Documenter la fonction utilitaire (inputs, outputs, exemples de prompts)
- Expliquer comment ajouter un nouveau cas métier (nouveau prompt, parsing, etc.)

## Bonus

- Permettre d'ajouter des pré/post-traitements spécifiques via des hooks/callbacks
- Mutualiser la gestion des erreurs et logs

---

## Checklist de progression

- [ ] Recenser tous les usages actuels de l'extraction PDF via LLM vision (devis, discounts, etc.)
- [ ] Lister les points communs et les différences
- [ ] Créer le module utilitaire `lib/llm_vision_extractor.py`
- [ ] Implémenter la fonction générique `extract_from_pdf_with_vision`
- [ ] Permettre le passage de prompts métier personnalisés
- [ ] Adapter le flag `.env` pour chaque usage (QUOTE_EXTRACTION_MODE, DISCOUNT_EXTRACTION_MODE)
- [ ] Refactorer l'extraction vision dans le module devis
- [ ] Refactorer l'extraction vision dans le module discounts
- [ ] Gérer le parsing métier du résultat dans chaque module
- [ ] Ajouter des tests unitaires pour la fonction générique
- [ ] Ajouter des tests d'intégration pour chaque usage métier
- [ ] Documenter la fonction utilitaire et les exemples de prompts
- [ ] Expliquer comment ajouter un nouveau cas métier

**Ce plan garantit une extraction PDF via LLM vision DRY, maintenable et facilement extensible à d'autres cas métier.**
