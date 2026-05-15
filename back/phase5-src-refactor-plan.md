# Phase 5 : Refactorisation de back/src

## Objectif
Restructurer back/src selon l'architecture propre avec couches bien définies :
- **api/** : HTTP handlers & routes
- **infrastructure/** : Clients externes & configurations (Supabase, Google, LLM, PDF, etc.)
- **domain/** : Modèles métier et entités (immutable, logic-free)
- **repository/** : Accès aux données
- **service/** : Logique métier
- **lib/** : Utilitaires & helpers réutilisables
- **tests/** : Tests en miroir (dans back/tests)

---

## Analyse des dossiers actuels

### ✅ À GARDER & RESTRUCTURER

#### 1. **api/** → API Layer ✓
- **Rôle** : HTTP request handlers, FastAPI routes
- **Décision** : GARDER & ENRICHIR
- **Action** : 
  - Vider et restructurer pour accueillir tous les handlers HTTP
  - Créer sous-dossiers par domaine : `api/auth/`, `api/business/`, `api/action/`, `api/quote/`, `api/product/`, `api/csv/`, `api/file/`
  - Chaque handler HTTP y va
  - Garder `__init__.py` pour exports

#### 2. **domain/** → Domain Layer ✓
- **Rôle** : Modèles métier (dataclasses, enums, value objects)
- **Contenu actuel** : `email.py`, `enums.py`, `opportunity.py`, `rfp.py`, `vendor.py`
- **Décision** : GARDER & ENRICHIR
- **Action** :
  - Ajouter les autres modèles métier qui manquent
  - Chaque entité = 1 fichier
  - NO LOGIC : juste structures + validation basique
  - Importer depuis d'autres modules vers domain/

#### 3. **repository/** → Data Access Layer ✓
- **Rôle** : Accès aux données (DB queries, abstraction)
- **Contenu actuel** : `action_repository.py`, `email_repository.py`, `opportunity.py`, `azure_oauth.py`
- **Décision** : GARDER & RÉORGANISER
- **Action** :
  - Structurer par aggregate root : `repository/action/`, `repository/email/`, `repository/opportunity/`, `repository/oauth/`
  - Éviter les mixed concerns
  - azure_oauth.py → peut aller dans infrastructure/ ou lib/auth/

#### 4. **service/** → Service/Business Logic Layer ✓
- **Rôle** : Logique métier, orchestration
- **Contenu actuel** : `action_executor.py`, `action_scheduler.py`
- **Décision** : GARDER & ENRICHIR
- **Action** :
  - Ajouter services manquants : email service, business service, classification service, etc.
  - Structurer par domaine métier
  - Services orchestrent repositories + infrastructure

#### 5. **infrastructure/** → External Clients & Factories ✓
- **Rôle** : Clients externes, configurations, factories
- **Contenu actuel** : `exceptions.py`, `factory.py`
- **Décision** : GARDER & ENRICHIR
- **Action** :
  - Créer sous-dossiers : `infrastructure/clients/`, `infrastructure/config/`
  - Déplacer tous les clients là : supabase, google_auth, google_drive, llm, pdf, embeddings, etc.
  - Chaque client = 1 module

#### 6. **lib/** → Shared Utilities (NEW)
- **Rôle** : Helpers, utilitaires, outils partagés
- **Création** : CRÉER
- **Contenu** : 
  - `lib/readers/` : reader/csv.py, reader/xls.py, text/reader.py, text/rfp_source_picker.py → fusionner logiquement
  - `lib/auth/` : google_auth logic
  - `lib/extractors/` : pdf extraction, text extraction
  - `lib/importers/` : fabdis, discount, net_price importers
  - `lib/calculations/` : net_price logic
  - `lib/encoders/` : embeddings
  - `lib/denormalizers/` : denormalizer.py
  - `lib/emails/` : domain/email.py peut aller ici ou domain

---

### 🗑️ À FUSIONNER/DÉPLACER

#### 7. **controller/** → À ÉCLATER ⚠️
- **Rôle** : Mélange de tout (handlers, clients, factories)
- **Décision** : ÉCLATER
- **Déplacements** :
  - `action_handlers.py` → `api/action/`
  - `business_handler.py` → `api/business/`
  - `classify_handler.py` → `api/classification/`
  - `csv_handlers.py` → `api/csv/`
  - `database_handlers.py` → `api/database/` (ou dans service si logique métier)
  - `email_handler.py` → `api/email/`
  - `file_handler.py` → `api/file/` ou `infrastructure/file/`
  - `handlers.py` → `api/router.py` ou `api/orchestrator.py` (point d'entrée)
  - `db_client.py` → `infrastructure/clients/database.py`
  - `auth/auth_handler.py` → `api/auth/`
  - `product/product.py` → `api/product/`
  - `quote/quote.py` → `api/quote/`
  - Clients/utils : `gmail_client.py`, `llm_factory.py`, `mime.py`, `multipart.py`, `rag.py` → `infrastructure/`

#### 8. **adapters/** → À ANALYSER
- **Rôle** : ? (probablement vide ou pour adaptateurs de format)
- **Décision** : À ANALYSER
- **Action** : Vérifier le contenu et décider

#### 9. **command/** → À GARDER MAIS RÉORGANISER
- **Rôle** : CLI entrypoints
- **Décision** : GARDER
- **Action** :
  - Rester à la racine de src/ ou créer dossier dédié
  - Utiliser service/ et repository/ au lieu d'importer depuis controller/
  - Nettoyer les imports après refactor

#### 10. **embeddings/** → LIB/ENCODERS ✓
- **Rôle** : Embedding generation
- **Décision** : DÉPLACER → `lib/encoders/embeddings.py`

#### 11. **etim/** → LIB/IMPORTERS ✓
- **Rôle** : Import utilities
- **Décision** : DÉPLACER → `lib/importers/etim.py`

#### 12. **fabdis/** → LIB/IMPORTERS ✓
- **Rôle** : Import utilities
- **Décision** : DÉPLACER → `lib/importers/fabdis.py`

#### 13. **google_auth/** → INFRASTRUCTURE ✓
- **Rôle** : Google auth client
- **Décision** : DÉPLACER → `infrastructure/clients/google_auth.py`
- **Action** : Fusionner avec `repository/azure_oauth.py` dans une couche d'authentification

#### 14. **google_drive/** → INFRASTRUCTURE ✓
- **Rôle** : Google Drive client
- **Décision** : DÉPLACER → `infrastructure/clients/google_drive.py`

#### 15. **llm/** → INFRASTRUCTURE ✓
- **Rôle** : LLM client
- **Décision** : DÉPLACER → `infrastructure/clients/llm.py`

#### 16. **net_price/** → LIB/CALCULATIONS ✓
- **Rôle** : Net price calculations
- **Décision** : DÉPLACER → `lib/calculations/net_price.py`

#### 17. **pdf/** → LIB/EXTRACTORS ✓
- **Rôle** : PDF text extraction
- **Décision** : DÉPLACER → `lib/extractors/pdf.py`

#### 18. **prompt/** → INFRASTRUCTURE/CONFIG ✓
- **Rôle** : Prompts management
- **Décision** : À ÉVALUER (probablement vide ?)
- **Action** : Si vide → supprimer; sinon → `infrastructure/prompts/`

#### 19. **reader/** → LIB/READERS ✓
- **Rôle** : CSV/XLS readers
- **Décision** : FUSIONNER → `lib/readers/`

#### 20. **supabase/** → INFRASTRUCTURE ✓
- **Rôle** : Supabase client (DB)
- **Décision** : DÉPLACER → `infrastructure/clients/supabase.py`

#### 21. **text/** → LIB/EXTRACTORS ✓
- **Rôle** : Text extraction & utilities
- **Décision** : DÉPLACER → `lib/extractors/text.py` ou fusionner avec reader/

#### 22. **utils/** → LIB ✓
- **Rôle** : Utilities (probablement vide ?)
- **Décision** : À ÉVALUER
- **Action** : Si contenu → fusionner dans lib/; sinon → supprimer

#### 23. **discount/** → LIB/IMPORTERS ✓
- **Rôle** : Import utilities
- **Décision** : DÉPLACER → `lib/importers/discount.py`

#### 24. **denormalizer/** → LIB/DATA ✓
- **Rôle** : Data denormalization utilities
- **Décision** : DÉPLACER → `lib/denormalizers/denormalizer.py`

---

## Nouvelle structure proposée

```
back/src/
├── api/                          # HTTP handlers & routes
│   ├── __init__.py
│   ├── router.py                 # Main orchestrator
│   ├── auth/
│   │   ├── __init__.py
│   │   └── handler.py            # Auth endpoints
│   ├── action/
│   │   ├── __init__.py
│   │   └── handler.py            # Action endpoints
│   ├── business/
│   │   ├── __init__.py
│   │   └── handler.py            # Business endpoints
│   ├── csv/
│   │   ├── __init__.py
│   │   └── handler.py            # CSV endpoints
│   ├── email/
│   │   ├── __init__.py
│   │   └── handler.py            # Email endpoints
│   ├── file/
│   │   ├── __init__.py
│   │   └── handler.py            # File upload endpoints
│   ├── product/
│   │   ├── __init__.py
│   │   └── handler.py            # Product endpoints
│   ├── quote/
│   │   ├── __init__.py
│   │   └── handler.py            # Quote endpoints
│   └── classification/
│       ├── __init__.py
│       └── handler.py            # Classification endpoints
│
├── infrastructure/               # External clients & configurations
│   ├── __init__.py
│   ├── exceptions.py             # Custom exceptions
│   ├── factory.py                # Service factory
│   ├── config.py                 # Configuration management
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── supabase.py           # Supabase client
│   │   ├── google_auth.py        # Google authentication
│   │   ├── google_drive.py       # Google Drive access
│   │   ├── llm.py                # LLM client
│   │   ├── database.py           # Generic DB handler
│   │   └── email.py              # Email service (SMTP)
│   └── prompts/                  # Prompt templates
│       ├── __init__.py
│       └── templates.py
│
├── domain/                       # Domain models & entities
│   ├── __init__.py
│   ├── email.py                  # Email entity
│   ├── enums.py                  # Domain enums
│   ├── opportunity.py            # Opportunity entity
│   ├── rfp.py                    # RFP entity
│   ├── vendor.py                 # Vendor entity
│   ├── action.py                 # Action entity
│   └── quote.py                  # Quote entity
│
├── repository/                   # Data access layer
│   ├── __init__.py
│   ├── action/
│   │   ├── __init__.py
│   │   └── repository.py
│   ├── email/
│   │   ├── __init__.py
│   │   └── repository.py
│   ├── opportunity/
│   │   ├── __init__.py
│   │   └── repository.py
│   ├── oauth/
│   │   ├── __init__.py
│   │   └── repository.py
│   └── base.py                   # Base repository interface
│
├── service/                      # Business logic & orchestration
│   ├── __init__.py
│   ├── action/
│   │   ├── __init__.py
│   │   ├── executor.py
│   │   └── scheduler.py
│   ├── email/
│   │   ├── __init__.py
│   │   └── service.py
│   ├── business/
│   │   ├── __init__.py
│   │   └── service.py
│   ├── classification/
│   │   ├── __init__.py
│   │   └── service.py
│   ├── quote/
│   │   ├── __init__.py
│   │   └── service.py
│   └── base.py                   # Base service interface
│
├── lib/                          # Shared utilities & helpers
│   ├── __init__.py
│   ├── readers/
│   │   ├── __init__.py
│   │   ├── csv.py
│   │   ├── xls.py
│   │   └── base.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── pdf.py
│   │   └── text.py
│   ├── encoders/
│   │   ├── __init__.py
│   │   └── embeddings.py
│   ├── calculations/
│   │   ├── __init__.py
│   │   └── net_price.py
│   ├── importers/
│   │   ├── __init__.py
│   │   ├── fabdis.py
│   │   ├── etim.py
│   │   ├── discount.py
│   │   └── base.py
│   ├── denormalizers/
│   │   ├── __init__.py
│   │   └── denormalizer.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── oauth.py
│   ├── email/
│   │   ├── __init__.py
│   │   ├── mime.py               # MIME utilities
│   │   └── multipart.py          # Multipart utilities
│   ├── formatting/
│   │   ├── __init__.py
│   │   └── utils.py              # Formatting utilities
│   └── common.py                 # Common utilities
│
└── command/                      # CLI entrypoints
    ├── __init__.py
    ├── action_cli.py
    ├── dev_server.py
    ├── email_cli.py
    ├── migrations_cli.py
    ├── regenerate_google_token.py
    ├── run_action_scheduler.py
    └── run_migration.py
```

---

## Tests en miroir

Structure parallèle dans `back/tests/` :

```
back/tests/
├── unit/
│   ├── api/
│   │   ├── auth/
│   │   ├── action/
│   │   ├── business/
│   │   ├── csv/
│   │   ├── email/
│   │   ├── file/
│   │   ├── product/
│   │   ├── quote/
│   │   └── classification/
│   ├── domain/
│   ├── repository/
│   │   ├── action/
│   │   ├── email/
│   │   ├── opportunity/
│   │   └── oauth/
│   ├── service/
│   │   ├── action/
│   │   ├── email/
│   │   ├── business/
│   │   ├── classification/
│   │   └── quote/
│   └── lib/
│       ├── readers/
│       ├── extractors/
│       ├── encoders/
│       ├── calculations/
│       ├── importers/
│       ├── denormalizers/
│       ├── auth/
│       ├── email/
│       └── formatting/
├── integration/
│   ├── api/
│   ├── action/
│   ├── business/
│   ├── email/
│   ├── classification/
│   ├── llm/
│   ├── qdrant/
│   └── pdf/
└── fixtures/
    ├── files/
    ├── data/
    └── mocks/
```

---

## Micro-commits à exécuter

### Phase 5.1 : Préparation (3-5 commits)
1. Créer nouvelle structure vide (dossiers)
2. Créer `__init__.py` dans tous les dossiers
3. Committer : `refactor(src): create phase 5 directory structure`

### Phase 5.2 : Migration des fichiers par couche (15-20 commits)
4-8. Déplacer infrastructure clients
9-12. Déplacer lib (readers, extractors, importers, etc.)
13-17. Restructurer api/ (éclater controller/)
18-20. Réorganiser repository/ par aggregate
21-23. Enrichir service/

### Phase 5.3 : Nettoyage & validation (5-10 commits)
24. Supprimer controller/ (après vérification complète)
25. Supprimer dossiers vidés (prompt, utils, adapters, etc.)
26. Mettre à jour imports dans command/ et autres
27. Compiler & tester
28. Documenter la nouvelle architecture

### Phase 5.4 : Tests en miroir (5-10 commits)
29-33. Créer structure tests en miroir
34-35. Déplacer & réorganiser fichiers tests existants
36-40. Ajouter tests manquants pour nouvelles structures

---

## Dépendances & ordre critique

```
command/ 
  ↓ (dépend de)
service/ & api/
  ↓
repository/ & infrastructure/
  ↓
domain/ & lib/
```

**Ordre d'exécution critique :**
1. ✅ Infrastructure clients d'abord (aucune dépendance interne)
2. ✅ Domain & lib (dépendent d'infrastructure)
3. ✅ Repository (dépend d'infrastructure & domain)
4. ✅ Service (dépend de repository, domain, lib)
5. ✅ Api (dépend de service, repository, domain, infrastructure)
6. ✅ Command (dépend de service)

---

## Décisions finales

| Dossier | Décision | Destination | Raison |
|---------|----------|------------|--------|
| `api/` | GARDER | api/ | Point d'entrée HTTP |
| `command/` | GARDER | command/ | CLI entrypoints |
| `controller/` | **ÉCLATER** | api/* + infrastructure/ | Mixed concerns |
| `domain/` | GARDER | domain/ | Domain models |
| `infrastructure/` | GARDER & ENRICHIR | infrastructure/clients/ | External clients |
| `repository/` | GARDER & RÉORGANISER | repository/* | Data access |
| `service/` | GARDER & ENRICHIR | service/* | Business logic |
| `adapters/` | ANALYSER | ? | À voir |
| `denormalizer/` | DÉPLACER | lib/denormalizers/ | Utility |
| `discount/` | DÉPLACER | lib/importers/ | Importer utility |
| `embeddings/` | DÉPLACER | lib/encoders/ | Encoder utility |
| `etim/` | DÉPLACER | lib/importers/ | Importer utility |
| `fabdis/` | DÉPLACER | lib/importers/ | Importer utility |
| `google_auth/` | DÉPLACER | infrastructure/clients/ | Client |
| `google_drive/` | DÉPLACER | infrastructure/clients/ | Client |
| `llm/` | DÉPLACER | infrastructure/clients/ | Client |
| `net_price/` | DÉPLACER | lib/calculations/ | Calculator utility |
| `pdf/` | DÉPLACER | lib/extractors/ | Extractor utility |
| `prompt/` | ÉVALUER | infrastructure/prompts/ | Config |
| `reader/` | DÉPLACER | lib/readers/ | Reader utility |
| `supabase/` | DÉPLACER | infrastructure/clients/ | Client |
| `text/` | DÉPLACER | lib/extractors/ | Extractor utility |
| `utils/` | ÉVALUER | lib/ | Utility |

---

## Prochaines étapes

1. **✅ Valider ce plan** : Discuter dossier par dossier
2. **Créer structure vide** : Commencer par micro-commit 1
3. **Migrer fichier par fichier** : Micro-commits atomiques
4. **Mettre à jour imports** : Par couche, dans l'ordre critique
5. **Tests en miroir** : Restructurer back/tests
6. **Validation & cleanup** : Compiler, tester, documenter
