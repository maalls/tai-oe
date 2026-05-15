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

## Décisions finales (✅ CONFIRMÉES)

| Dossier | Décision | Destination | Action |
|---------|----------|------------|--------|
| `api/` | ✅ GARDER & RÉORG | api/auth, action, business, email, csv, file, product, quote, classification, prompt/ | Restructurer par domaine |
| `command/` | ✅ GARDER | command/ | Laisser comme est (CLI entrypoints) |
| `controller/` | ✅ **ÉCLATER** | api/* + infrastructure/ + lib/ | 16 fichiers → destinations ciblées |
| `domain/` | ✅ ENRICHIR | domain/ | Ajouter action, quote, product, business, classification |
| `infrastructure/` | ✅ RESTRUCTURER | infrastructure/clients/, config/, prompts/, exceptions.py, factory.py | Créer sous-structure |
| `repository/` | ✅ RESTRUCTURER | repository/action/, email/, opportunity/, oauth/, contracts/ | Organiser par aggregate + MOVE classifier |
| `service/` | ✅ ENRICHIR | service/action/, email/, business/, classification/, quote/ | Créer services manquants |
| `adapters/` | ✅ **SUPPRIMER** | FUSED into lib/email/ | Fusionner parser HTML → lib/email/html_parser.py |
| `denormalizer/` | ✅ DÉPLACER | lib/denormalizers/ | Move denormalizer.py |
| `discount/` | ✅ DÉPLACER | lib/importers/ | Move importer.py |
| `embeddings/` | ✅ DÉPLACER | lib/encoders/ | Move embeddings.py |
| `etim/` | ✅ DÉPLACER | lib/importers/ | Move etim.py |
| `fabdis/` | ✅ DÉPLACER | lib/importers/ | Move importer.py |
| `google_auth/` | ✅ DÉPLACER | infrastructure/clients/ | Move google_auth.py |
| `google_drive/` | ✅ DÉPLACER | infrastructure/clients/ | Move gdrive_tool.py + helpers |
| `llm/` | ✅ DÉPLACER | infrastructure/clients/ | Move client.py |
| `net_price/` | ✅ DÉPLACER | lib/calculations/ | Move importer.py |
| `pdf/` | ✅ DÉPLACER | lib/extractors/ | Move extract_text.py |
| `prompt/` | ✅ **CENTRALISER** | infrastructure/prompts/ | Move prompt.md files |
| `reader/` | ✅ DÉPLACER | lib/readers/ | Move csv.py, xls.py |
| `supabase/` | ✅ DÉPLACER | infrastructure/clients/ | Move supabase_client.py |
| `text/` | ✅ DÉPLACER | lib/extractors/ | Move reader.py, rfp_source_picker.py |
| `utils/` | ✅ **SUPPRIMER** | FUSED into lib/email/ | Fusionner EmailHTMLParser → lib/email/html_parser.py |

---

## ✅ DÉCISIONS FINALES (Session d'analyse complète)

### Session de Q&A résumé :

#### adapters/ & utils/
- **DÉCISION** : Fusionner HTML parser dans `lib/email/html_parser.py`, **SUPPRIMER** dossiers vides
- **Action** : Move `adapters/email/html/parser.py` + `utils/Email/HTMLParser/EmailHTMLParser.py` → `lib/email/html_parser.py` (fusion)

#### prompt/
- **DÉCISION** : **CENTRALISER** dans `infrastructure/prompts/` (utilisé par controller/handlers.py, rag.py, text/reader.py)
- **Action** : Move `back/src/prompt/opportunity/source/prompt.md` → `infrastructure/prompts/opportunity/source/prompt.md`

#### controller/
- **DÉCISION** : **ÉCLATER COMPLÈTEMENT** (16 fichiers) selon rôle :
  - Handlers HTTP → `api/*` (9 handlers)
  - Clients & factories → `infrastructure/clients/` (db_client.py) + `infrastructure/factory.py` (llm_factory.py)
  - Utilitaires → `lib/email/` (mime.py, multipart.py)
  - rag.py → `api/prompt/handler.py`
- **Action** : Migration fichier par fichier avec mise à jour imports

#### repository/
- **DÉCISION** : **RESTRUCTURER** par aggregate root + **MOVE classifier** vers service/
  - Plat → Organisé : action/, email/, opportunity/, oauth/ (chacun avec repository.py)
  - **GARDER** `repository/contracts/` (interfaces abstraites)
  - **MOVE** `repository/classifier/classifier.py` → `service/classification/service.py` (c'est un service, pas un repository)
- **Action** : Micro-commits par aggregate

#### domain/
- **DÉCISION** : **ENRICHIR** avec entities manquantes (action.py, quote.py, product.py, business.py, classification.py)
- **Action** : Créer fichiers entities vides avec structures minimales

#### service/
- **DÉCISION** : **CRÉER** services manquants pour : Email, Business, Classification, Quote, Product (actuellement logique dans controller/)
- **Action** : Créer structures services avec services.py vides, remplir lors du refactor

#### infrastructure/
- **DÉCISION** : **RESTRUCTURER** en couches :
  - `infrastructure/clients/` : tous les clients externes (supabase, google_auth, google_drive, llm, email SMTP, database)
  - `infrastructure/config/` : configuration management
  - `infrastructure/prompts/` : centraliser tous les prompts
  - `infrastructure/exceptions.py`, `infrastructure/factory.py` : garder
- **Action** : Créer structure, déplacer fichiers (20+ migrations)

#### lib/ (NEW)
- **DÉCISION** : **CRÉER** nouvelle couche utilitaires partagés :
  - `lib/readers/` : csv.py, xls.py
  - `lib/extractors/` : pdf.py, text.py, email_html_parser.py (fusionné)
  - `lib/encoders/` : embeddings.py
  - `lib/calculations/` : net_price.py
  - `lib/importers/` : fabdis/, etim/, discount/
  - `lib/denormalizers/` : denormalizer.py
  - `lib/auth/` : oauth.py (moved from repository/)
  - `lib/email/` : mime.py, multipart.py, html_parser.py (fusionné)
  - `lib/formatting/` : formatting utils
- **Action** : Créer structure complète, déplacer 10+ dossiers/fichiers

#### api/
- **DÉCISION** : Restructurer par domaine (9 domaines) + créer `api/prompt/`
  - Auth, Action, Business, Email, CSV, File, Product, Quote, Classification, Prompt
- **Action** : Éclater controller/ et réorganiser handlers

#### Dossiers à SUPPRIMER (après migration)
- ✅ adapters/
- ✅ utils/
- ✅ controller/ (après migration complète)
- ✅ embeddings/, etim/, fabdis/, google_auth/, google_drive/, llm/, net_price/, pdf/, reader/, supabase/, text/, discount/, denormalizer/
- ✅ prompt/ (après centralisation)

---

## Prochaines étapes

1. **✅ Session Q&A complète** : TERMINÉE
2. **Créer structure vide** : Phase 5.1 (3-5 commits)
3. **Migrer fichier par fichier** : Phase 5.2 (20-30 commits)
4. **Mettre à jour imports** : Phase 5.3 (5-10 commits)
5. **Tests en miroir** : Phase 5.4 (5-10 commits)
6. **Validation & cleanup** : Phase 5.5 (5-10 commits)
