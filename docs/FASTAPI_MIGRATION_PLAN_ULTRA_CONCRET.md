# Plan Ultra Concret - Migration Progressive vers FastAPI

## Objectif

Découper `back/src/api/server.py` en domaines FastAPI, sans Big Bang, avec rollback simple à chaque étape.

## Fenêtre de migration

- Début: 2026-05-18
- Fin: 2026-06-26
- Durée: 6 semaines

## Résultat attendu à la fin

- Le serveur principal est FastAPI.
- Les endpoints migrés sont couverts par tests unitaires + tests de parité.
- Les routes legacy restantes (si besoin) sont isolées et planifiées pour suppression.

---

## Règles d'exécution (obligatoires)

1. Un lot de migration = 2 à 5 endpoints max.
2. Un lot n'est mergeable que si:
   - tests unitaires verts,
   - tests de parité verts,
   - rollback documenté.
3. Ne pas réécrire la logique métier pendant la migration.
4. Chaque endpoint migré garde son contrat HTTP (code + payload) tant qu'aucune évolution fonctionnelle n'est validée.

---

## Architecture cible minimale

### Cible technique

- App FastAPI dédiée: `back/src/api/fastapi_app.py`
- Router par domaine:
  - `back/src/api/email/routes.py`
  - `back/src/api/opportunity/routes.py`
  - `back/src/api/rfq/routes.py`
- Schémas Pydantic par domaine:
  - `back/src/api/email/schemas.py`
  - `back/src/api/opportunity/schemas.py`
  - `back/src/api/rfq/schemas.py`

### Compatibilité

- Coexistence legacy + FastAPI pendant migration.
- Activation par domaine via feature flags de routage.

---

## Planning détaillé (début -> fin)

## Semaine 1 (2026-05-18 -> 2026-05-22) - Baseline + Squelette

### Livrables

1. Inventaire complet des routes de `server.py`.
2. App FastAPI bootable sur port dédié (dev).
3. Premier router branché (`email`) avec endpoints read-only simples.
4. Matrice de parité des routes (legacy vs FastAPI).

### Tâches concrètes

1. Créer `back/src/api/fastapi_app.py`:
   - initialiser `FastAPI(...)`,
   - inclure `email.routes`,
   - ajouter `/health`.
2. Ajouter script run dev FastAPI (ex: `uvicorn ... --port 8089`).
3. Créer document d'inventaire:
   - `docs/API_ROUTE_INVENTORY.md`
   - colonnes: method, path, handler legacy, domaine, priorité, statut migration.
4. Écrire tests smoke FastAPI:
   - `back/tests/unit/api/test_fastapi_health.py`
   - `back/tests/unit/api/email/test_email_routes_smoke.py`

### Critère de sortie S1

- FastAPI démarre localement.
- Inventaire 100% rempli.
- 1er lot read-only email validé.

---

## Semaine 2 (2026-05-25 -> 2026-05-29) - Domaine Email complet

### Livrables

1. Migration des routes email restantes (read + write).
2. Schémas Pydantic email.
3. Tests unitaires et parité email.

### Tâches concrètes

1. Finaliser `back/src/api/email/routes.py`.
2. Créer `back/src/api/email/schemas.py` (requests/responses).
3. Réutiliser les handlers/services existants:
   - `back/src/api/email/handler.py`
   - `back/src/service/email/*`
4. Ajouter tests:
   - `back/tests/unit/api/email/*` (routes),
   - `back/tests/unit/service/email/*` (si adaptation),
   - `back/tests/integration/api/email/*` (parité).

### Critère de sortie S2

- Toutes les routes email ciblées répondent via FastAPI.
- Aucun écart de contrat non documenté.
- Suite email verte.

---

## Semaine 3 (2026-06-01 -> 2026-06-05) - Opportunity read-only

### Livrables

1. Router FastAPI opportunity (lecture).
2. Schémas Pydantic opportunity lecture.
3. Tests de parité endpoints lecture.

### Tâches concrètes

1. Créer `back/src/api/opportunity/routes.py` (GET uniquement).
2. Créer `back/src/api/opportunity/schemas.py`.
3. Mapper vers logique existante (handlers/services actuels).
4. Ajouter tests:
   - `back/tests/unit/api/opportunity/*` pour routes GET,
   - `back/tests/integration/api/opportunity/*` pour parité.

### Critère de sortie S3

- Endpoints opportunity GET basculables sans impact.

---

## Semaine 4 (2026-06-08 -> 2026-06-12) - Opportunity write

### Livrables

1. POST/PATCH/DELETE opportunity via FastAPI.
2. Validation stricte Pydantic.
3. Gestion erreurs uniforme.

### Tâches concrètes

1. Étendre `back/src/api/opportunity/routes.py` avec write endpoints.
2. Ajouter normalisation d'erreurs HTTP (400/404/422/500) cohérente.
3. Tests:
   - unitaires write,
   - intégration write,
   - tests de non-régression métier.

### Critère de sortie S4

- Flux opportunity complet (read + write) stable en FastAPI.

---

## Semaine 5 (2026-06-15 -> 2026-06-19) - RFQ + routes annexes

### Livrables

1. Migration RFQ.
2. Migration routes annexes (status, utilitaires, endpoints isolés).
3. Baisse significative du trafic legacy.

### Tâches concrètes

1. Créer `back/src/api/rfq/routes.py` + `schemas.py`.
2. Migrer endpoints upload/traitement RFQ.
3. Migrer endpoints annexes à faible dépendance.
4. Ajouter tests de parité et robustesse payload.

### Critère de sortie S5

- Tous les domaines principaux sont disponibles côté FastAPI.

---

## Semaine 6 (2026-06-22 -> 2026-06-26) - Bascule finale + Nettoyage

### Livrables

1. FastAPI devient point d'entrée principal.
2. Legacy isolé en fallback temporaire.
3. Plan de suppression définitive legacy.

### Tâches concrètes

1. Mettre FastAPI comme serveur par défaut.
2. Conserver fallback legacy derrière flag (durée limitée).
3. Nettoyer code mort et routes non utilisées.
4. Mettre à jour la doc d'exploitation:
   - run local,
   - run prod,
   - procédure rollback.

### Critère de sortie S6 (fin)

- FastAPI en production par défaut.
- Monitoring stable.
- Aucun blocker ouvert de migration.

---

## Plan de feature flags (progressif)

### Flags proposés

- `USE_FASTAPI_EMAIL`
- `USE_FASTAPI_OPPORTUNITY`
- `USE_FASTAPI_RFQ`
- `USE_FASTAPI_DEFAULT`

### Politique

1. Activer un domaine à la fois.
2. Observer erreurs/latence 24h.
3. Si anomalie: rollback immédiat via flag.

---

## Stratégie de tests (à appliquer à chaque lot)

### Minimum obligatoire

1. Unit tests route FastAPI.
2. Unit tests service impacté.
3. Tests de parité legacy vs FastAPI sur cas nominaux + erreurs principales.

### Commandes de validation type

1. `pytest tests/unit/api/email tests/unit/service/email -q`
2. `pytest tests/unit/api/opportunity tests/unit/service/opportunity -q`
3. `pytest tests/integration/api -q`

---

## Checklist PR (copier-coller)

1. Endpoints migrés listés explicitement.
2. Contrat HTTP inchangé ou diff documenté.
3. Schémas Pydantic ajoutés/mis à jour.
4. Tests unitaires ajoutés/mis à jour.
5. Tests de parité ajoutés/mis à jour.
6. Feature flag et rollback précisés.
7. Documentation runbook mise à jour.

---

## Risques principaux et contre-mesures

1. Dérive de contrat API:
   - Contre-mesure: tests de parité systématiques.
2. Mélange refacto + migration:
   - Contre-mesure: PR migration sans refacto métier.
3. Régression silencieuse:
   - Contre-mesure: rollout progressif + observabilité + rollback flag.

---

## Jalons de pilotage

1. Jalon A (fin S1): socle FastAPI opérationnel.
2. Jalon B (fin S2): domaine email terminé.
3. Jalon C (fin S4): opportunity terminé.
4. Jalon D (fin S5): RFQ + annexes terminés.
5. Jalon E (fin S6): bascule finale et fermeture du plan.

---

## Début et fin du plan

- Début opérationnel: 2026-05-18 (Sprint S1 lancé)
- Fin opérationnelle: 2026-06-26 (FastAPI par défaut + legacy en extinction contrôlée)
