# FastAPI Migration - Execution Kanban

Document de suivi opérationnel basé sur le plan principal.

- Plan source: docs/FASTAPI_MIGRATION_PLAN_ULTRA_CONCRET.md
- Début: 2026-05-18
- Fin: 2026-06-26
- Owner global: TBD
- Statut global: Not started

## Légende

- [ ] Not started
- [~] In progress
- [x] Done
- [!] Blocked

---

## 0) Préparation immédiate (avant S1)

- [ ] Nommer un owner technique migration
  - Owner: TBD
  - Due: 2026-05-16
  - Critère: nom validé et partagé
- [ ] Nommer un backup owner
  - Owner: TBD
  - Due: 2026-05-16
  - Critère: backup documenté
- [ ] Créer canal de suivi quotidien (Slack/Teams/Notion)
  - Owner: TBD
  - Due: 2026-05-16
  - Critère: lien de canal ajouté ici
- [ ] Ajouter ce fichier aux rituels équipe
  - Owner: TBD
  - Due: 2026-05-16
  - Critère: revue quotidienne active

---

## 1) Semaine 1 - Baseline + Squelette (2026-05-18 -> 2026-05-22)

### 1.1 Inventaire routes

- [ ] Créer docs/API_ROUTE_INVENTORY.md
  - Owner: TBD
  - Due: 2026-05-19
- [ ] Lister 100% des routes de back/src/api/server.py
  - Owner: TBD
  - Due: 2026-05-19
- [ ] Remplir colonnes: method, path, handler legacy, domaine, priorité, statut
  - Owner: TBD
  - Due: 2026-05-20
- [ ] Valider inventaire en revue pair
  - Owner: TBD
  - Due: 2026-05-20

### 1.2 App FastAPI bootable

- [ ] Créer back/src/api/fastapi_app.py
  - Owner: TBD
  - Due: 2026-05-20
- [ ] Ajouter endpoint /health
  - Owner: TBD
  - Due: 2026-05-20
- [ ] Inclure router email
  - Owner: TBD
  - Due: 2026-05-21
- [ ] Ajouter commande de lancement dev (port dédié ex 8089)
  - Owner: TBD
  - Due: 2026-05-21

### 1.3 Tests smoke FastAPI

- [ ] Créer back/tests/unit/api/test_fastapi_health.py
  - Owner: TBD
  - Due: 2026-05-21
- [ ] Créer back/tests/unit/api/email/test_email_routes_smoke.py
  - Owner: TBD
  - Due: 2026-05-22
- [ ] Vérifier passage des tests smoke en CI locale
  - Owner: TBD
  - Due: 2026-05-22

### Gate S1

- [ ] FastAPI démarre localement
- [ ] Inventaire complet validé
- [ ] Premier lot read-only email prêt

---

## 2) Semaine 2 - Domaine Email complet (2026-05-25 -> 2026-05-29)

### 2.1 Routes + schémas

- [ ] Finaliser back/src/api/email/routes.py
  - Owner: TBD
  - Due: 2026-05-26
- [ ] Créer/compléter back/src/api/email/schemas.py
  - Owner: TBD
  - Due: 2026-05-26
- [ ] Brancher handlers existants (pas de refacto métier)
  - Owner: TBD
  - Due: 2026-05-27

### 2.2 Tests email

- [ ] Couvrir routes email unitaires
  - Owner: TBD
  - Due: 2026-05-28
- [ ] Mettre à jour tests service email impactés
  - Owner: TBD
  - Due: 2026-05-28
- [ ] Ajouter tests de parité legacy vs FastAPI email
  - Owner: TBD
  - Due: 2026-05-29

### 2.3 Validation lot S2

- [ ] Exécuter: pytest tests/unit/api/email tests/unit/service/email -q
- [ ] Exécuter: pytest tests/integration/api/email -q
- [ ] Documenter écarts de contrat éventuels

### Gate S2

- [ ] Toutes routes email ciblées répondent via FastAPI
- [ ] Aucun écart non documenté
- [ ] Suite email verte

---

## 3) Semaine 3 - Opportunity read-only (2026-06-01 -> 2026-06-05)

### 3.1 Implémentation

- [ ] Créer back/src/api/opportunity/routes.py (GET)
  - Owner: TBD
  - Due: 2026-06-02
- [ ] Créer back/src/api/opportunity/schemas.py (GET)
  - Owner: TBD
  - Due: 2026-06-02
- [ ] Mapper vers logique existante
  - Owner: TBD
  - Due: 2026-06-03

### 3.2 Tests

- [ ] Ajouter tests unitaires GET opportunity
  - Owner: TBD
  - Due: 2026-06-04
- [ ] Ajouter tests de parité GET opportunity
  - Owner: TBD
  - Due: 2026-06-05

### Gate S3

- [ ] Endpoints opportunity GET basculables sans impact

---

## 4) Semaine 4 - Opportunity write (2026-06-08 -> 2026-06-12)

### 4.1 Implémentation

- [ ] Ajouter POST/PATCH/DELETE dans back/src/api/opportunity/routes.py
  - Owner: TBD
  - Due: 2026-06-10
- [ ] Ajouter validation Pydantic write
  - Owner: TBD
  - Due: 2026-06-10
- [ ] Uniformiser gestion erreurs HTTP (400/404/422/500)
  - Owner: TBD
  - Due: 2026-06-11

### 4.2 Tests

- [ ] Ajouter tests unitaires write opportunity
  - Owner: TBD
  - Due: 2026-06-11
- [ ] Ajouter tests intégration write opportunity
  - Owner: TBD
  - Due: 2026-06-12
- [ ] Vérifier non-régression métier
  - Owner: TBD
  - Due: 2026-06-12

### Gate S4

- [ ] Flux opportunity complet stable en FastAPI

---

## 5) Semaine 5 - RFQ + annexes (2026-06-15 -> 2026-06-19)

### 5.1 Implémentation

- [ ] Créer back/src/api/rfq/routes.py
  - Owner: TBD
  - Due: 2026-06-16
- [ ] Créer back/src/api/rfq/schemas.py
  - Owner: TBD
  - Due: 2026-06-16
- [ ] Migrer endpoints upload/traitement RFQ
  - Owner: TBD
  - Due: 2026-06-18
- [ ] Migrer routes annexes faible dépendance
  - Owner: TBD
  - Due: 2026-06-19

### 5.2 Tests

- [ ] Ajouter tests unitaires RFQ
  - Owner: TBD
  - Due: 2026-06-19
- [ ] Ajouter tests parité RFQ + annexes
  - Owner: TBD
  - Due: 2026-06-19

### Gate S5

- [ ] Domaines principaux disponibles côté FastAPI

---

## 6) Semaine 6 - Bascule finale + nettoyage (2026-06-22 -> 2026-06-26)

### 6.1 Bascule

- [ ] Activer FastAPI comme point d'entrée par défaut
  - Owner: TBD
  - Due: 2026-06-23
- [ ] Conserver fallback legacy temporaire derrière flag
  - Owner: TBD
  - Due: 2026-06-23

### 6.2 Stabilisation

- [ ] Monitoring erreurs et latence 24h
  - Owner: TBD
  - Due: 2026-06-24
- [ ] Corriger écarts critiques détectés
  - Owner: TBD
  - Due: 2026-06-25

### 6.3 Nettoyage

- [ ] Nettoyer code mort principal
  - Owner: TBD
  - Due: 2026-06-26
- [ ] Mettre à jour runbook (dev/prod/rollback)
  - Owner: TBD
  - Due: 2026-06-26
- [ ] Planifier suppression définitive legacy
  - Owner: TBD
  - Due: 2026-06-26

### Gate S6 (fin)

- [ ] FastAPI par défaut
- [ ] Monitoring stable
- [ ] Aucun blocker migration ouvert

---

## 7) Feature flags et rollout

- [ ] Définir USE_FASTAPI_EMAIL
- [ ] Définir USE_FASTAPI_OPPORTUNITY
- [ ] Définir USE_FASTAPI_RFQ
- [ ] Définir USE_FASTAPI_DEFAULT
- [ ] Activer un domaine à la fois
- [ ] Observation 24h entre activations
- [ ] Procédure rollback testée

---

## 8) Checklist PR obligatoire (à répéter pour chaque lot)

- [ ] Endpoints migrés listés explicitement
- [ ] Contrat HTTP inchangé ou diff documenté
- [ ] Schémas Pydantic ajoutés/mis à jour
- [ ] Tests unitaires ajoutés/mis à jour
- [ ] Tests parité ajoutés/mis à jour
- [ ] Feature flag + rollback précisés
- [ ] Runbook mis à jour

---

## 9) Journal de progression

## 2026-05-15

- Statut global: Not started
- Dernière action: création du Kanban d'exécution
- Prochaine action: nommer owner + lancer S1.1

## 2026-05-16

- Statut global:
- Dernière action:
- Prochaine action:

## 2026-05-19

- Statut global:
- Dernière action:
- Prochaine action:

## 2026-05-22

- Statut global:
- Dernière action:
- Prochaine action:

## 2026-05-29

- Statut global:
- Dernière action:
- Prochaine action:

## 2026-06-05

- Statut global:
- Dernière action:
- Prochaine action:

## 2026-06-12

- Statut global:
- Dernière action:
- Prochaine action:

## 2026-06-19

- Statut global:
- Dernière action:
- Prochaine action:

## 2026-06-26

- Statut global:
- Dernière action:
- Clôture:
