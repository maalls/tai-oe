# backend.refactor.2.plan

## objectif

Refactorer vers FastAPI a partir de l'inventaire des appels frontend pour les domaines:

- opportunity
- rfq
- quote
- client
- contact
- account
- vendor
- brand
- family
- product

Le plan fixe une regle unique: **toutes les APIs HTTP listees ci-dessous doivent etre migrees vers FastAPI**.

Hors scope immediat (mis de cote pour cette phase):

- appels frontend en `supabase-direct`

## regles de lecture

- `transport=fastapi`: endpoint deja servi par `back/src/api_fastapi/**`
- `transport=legacy`: endpoint servi par `back/src/api/**`
- `transport=unknown`: endpoint appele par le frontend mais non trouve tel quel dans les routers actuels

## inventaire complet des appels frontend (scope demande)

### 1) appels HTTP frontend (fetch/apiUrl)

| domaine       | endpoint (pattern)                           | methode | transport actuel | evidence frontend                                                                                                                                                                                     | backend owner actuel                         | decision |
| ------------- | -------------------------------------------- | ------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | -------- |
| opportunity   | `/api/opportunities/search`                  | GET     | fastapi          | `front/src/components/opportunity/IndexPage.vue`                                                                                                                                                      | `back/src/api_fastapi/opportunity/router.py` | migre    |
| opportunity   | `/api/opportunities/create-manual`           | POST    | fastapi          | `front/src/components/opportunity/IndexPage.vue`                                                                                                                                                      | `back/src/api_fastapi/opportunity/router.py` | migre    |
| opportunity   | `/api/opportunities/create-from-email`       | POST    | fastapi          | `front/src/components/mail/IndexPage.vue`                                                                                                                                                             | `back/src/api_fastapi/opportunity/router.py` | migre    |
| opportunity   | `/api/opportunities/{ids}`                   | DELETE  | fastapi          | `front/src/components/opportunity/IndexPage.vue`                                                                                                                                                      | `back/src/api_fastapi/opportunity/router.py` | migre    |
| opportunity   | `/api/opportunities/{id}`                    | DELETE  | fastapi          | `front/src/components/opportunity/components/settings/SettingsPage.vue`                                                                                                                               | `back/src/api_fastapi/opportunity/router.py` | migre    |
| opportunity   | `/api/opportunity`                           | GET     | fastapi          | `front/src/components/opportunity/OpportunityHeader.vue`, `front/src/components/opportunity/components/settings/SettingsPage.vue`                                                                     | `back/src/api_fastapi/opportunity/router.py` | migre    |
| rfq           | `/api/opportunity/{id}/rfq/generate`         | POST    | fastapi          | `front/src/components/opportunity/components/quote/Quote.vue`                                                                                                                                         | `back/src/api_fastapi/opportunity/router.py` | migre    |
| rfq           | `/api/opportunity/{id}/rfq/create-from-text` | POST    | fastapi          | `front/src/components/opportunity/components/source/SourcePage.ts`                                                                                                                                    | `back/src/api_fastapi/opportunity/router.py` | migre    |
| quote         | `/api/quote/{document_id}`                   | POST    | fastapi          | `front/src/components/opportunity/components/quote/Quote.vue`                                                                                                                                         | `back/src/api_fastapi/quote/router.py`       | migre    |
| quote         | `/api/quote/{document_id}/pdf`               | POST    | fastapi          | `front/src/components/opportunity/components/quote/Quote.vue`, `front/src/components/opportunity/components/send/SendPage.vue`                                                                        | `back/src/api_fastapi/quote/router.py`       | migre    |
| quote         | `/api/quotes/download/{filename}`            | GET     | fastapi          | `front/src/components/opportunity/components/send/SendPage.vue`, `front/src/components/opportunity/components/preview/PreviewPage.vue`                                                                | `back/src/api_fastapi/quote/router.py`       | migre    |
| quote         | `/api/opportunity/{id}/send-quote`           | POST    | fastapi          | `front/src/components/opportunity/components/send/SendPage.vue`                                                                                                                                       | `back/src/api_fastapi/opportunity/router.py` | migre    |
| quote         | `/api/quote/{opportunity_id}/generate`       | POST    | fastapi          | `front/src/components/opportunity/components/pipeline/components/PipelineStageRfp/PipelineStageRfp.vue`                                                                                               | `back/src/api_fastapi/quote/router.py`       | migre    |
| quote/invoice | `/api/quote/{id}/invoice`                    | POST    | fastapi          | `front/src/components/opportunity/components/pipeline/components/PipelineStageAccepted/PipelineStageAccepted.vue`, `front/src/components/opportunity/components/pipeline/components/StageManager.vue` | `back/src/api_fastapi/quote/router.py`       | migre    |
| contact/doc   | `/api/document/extract-rfp`                  | POST    | fastapi          | `front/src/components/opportunity/components/source/SourcePage.ts`                                                                                                                                    | `back/src/api_fastapi/document/router.py`    | migre    |
| contact/doc   | `/api/document/update-content`               | POST    | fastapi          | `front/src/components/opportunity/components/source/SourcePage.ts`                                                                                                                                    | `back/src/api_fastapi/document/router.py`    | migre    |
| contact/doc   | `/api/document/{id}`                         | DELETE  | fastapi          | `front/src/components/opportunity/components/documents/DocumentsPage.vue`                                                                                                                             | `back/src/api_fastapi/document/router.py`    | migre    |
| contact/doc   | `/api/chat/attachments`                      | POST    | fastapi          | `front/src/components/chat/ChatPanel.ts`                                                                                                                                                              | `back/src/api_fastapi/document/router.py`    | migre    |
| vendor        | `/api/vendor`                                | GET     | fastapi          | `front/src/components/vendor/Edit.vue`                                                                                                                                                                | `back/src/api_fastapi/vendor/router.py`      | migre    |
| product       | `/api/products`                              | POST    | fastapi          | `front/src/components/products/edit.vue`                                                                                                                                                              | `back/src/api_fastapi/product/router.py`     | migre    |
| product       | `/api/products/{id}`                         | GET/PUT | fastapi          | `front/src/components/products/edit.vue`                                                                                                                                                              | `back/src/api_fastapi/product/router.py`     | migre    |

### 2) parking lot (hors scope immediat): supabase-direct

Ces flux sont explicitement reportes apres la migration HTTP vers FastAPI.

| domaine     | statut  |
| ----------- | ------- |
| opportunity | reporte |
| rfq         | reporte |
| quote       | reporte |
| client      | reporte |
| contact     | reporte |
| account     | reporte |
| vendor      | reporte |
| brand       | reporte |
| family      | reporte |
| product     | reporte |

## backlog refactor vers FastAPI (propose)

### lot A - opportunity/rfq coeur

1. fait: migrer `/api/opportunities/search` (GET)
2. fait: migrer `/api/opportunities/create-manual` (POST)
3. fait: migrer `/api/opportunities/create-from-email` (POST)
4. fait: migrer `/api/opportunities/{id|ids}` (DELETE)
5. fait: migrer `/api/opportunity/{id}/rfq/generate` et `/api/opportunity/{id}/rfq/create-from-text`

### lot B - quote/invoice legacy restants

1. fait: migrer `/api/opportunity/{id}/send-quote`
2. fait: migrer `/api/quote/{id}/invoice`
3. fait: migrer `/api/invoice/{id}/pdf`
4. fait: migrer `/api/invoice/{id}/send`
5. fait: migrer `/api/quote/{opportunity_id}/generate`

### lot C - document/contact flows

1. fait: migrer `/api/document/extract-rfp`
2. fait: migrer `/api/document/update-content`
3. fait: migrer `/api/document/{id}` (DELETE)
4. fait: migrer `/api/chat/attachments`

### lot D - product/vendor/brand/family/account/contact

1. preparer les endpoints HTTP manquants uniquement
2. creer endpoints FastAPI minimaux pour operations critiques retenues
3. migrer ecran par ecran avec tests de parite
4. traiter `supabase-direct` dans une phase ulterieure dediee

## suivi de progression (section de pilotage)

### snapshot global

- domaines cibles: 10
- domaines clotures: 6/10
- endpoints HTTP legacy a migrer (dans ce scope): 0
- endpoints HTTP unknown a implementer: 0
- supabase-direct: hors scope immediat (10 domaines reportes)

### tableau de progression par domaine

| domaine     | HTTP FastAPI | HTTP legacy restant | unknown | statut     | notes                                    |
| ----------- | ------------ | ------------------- | ------- | ---------- | ---------------------------------------- |
| opportunity | oui          | non                 | non     | migre      | lot A migre en FastAPI                   |
| rfq         | oui          | non                 | non     | migre      | routes opportunity/\*/rfq migrees        |
| quote       | oui          | non                 | non     | migre      | endpoint quote/generate migre FastAPI    |
| client      | non          | non                 | non     | a trancher | pas d'appel HTTP explicite detecte       |
| contact     | oui          | non                 | non     | migre      | document/chat migres en FastAPI          |
| account     | non          | non                 | non     | a trancher | principalement supabase-direct (reporte) |
| vendor      | oui          | non                 | non     | migre      | endpoint /api/vendor migre FastAPI       |
| brand       | non          | non                 | non     | a trancher | principalement supabase-direct (reporte) |
| family      | non          | non                 | non     | a trancher | principalement supabase-direct (reporte) |
| product     | oui          | non                 | non     | migre      | GET/PUT/POST produits migres FastAPI     |

### journal des decisions

- format attendu: `YYYY-MM-DD | domaine | endpoint | decision=migrer | rationale`
- 2026-05-18 | global | tous les endpoints HTTP listes | decision=migrer | directive: toutes les API notees doivent etre migrees
- 2026-05-18 | opportunity | /api/opportunities/search | decision=migrer | endpoint implemente dans back/src/api_fastapi/opportunity/router.py
- 2026-05-18 | opportunity | /api/opportunities/create-manual | decision=migrer | endpoint implemente dans back/src/api_fastapi/opportunity/router.py
- 2026-05-18 | opportunity | /api/opportunities/create-from-email | decision=migrer | endpoint implemente dans back/src/api_fastapi/opportunity/router.py
- 2026-05-18 | opportunity | /api/opportunities/{id|ids} | decision=migrer | endpoint implemente dans back/src/api_fastapi/opportunity/router.py
- 2026-05-18 | rfq | /api/opportunity/{id}/rfq/generate | decision=migrer | endpoint implemente dans back/src/api_fastapi/opportunity/router.py
- 2026-05-18 | rfq | /api/opportunity/{id}/rfq/create-from-text | decision=migrer | endpoint implemente dans back/src/api_fastapi/opportunity/router.py
- 2026-05-18 | quote | /api/opportunity/{id}/send-quote | decision=migrer | endpoint implemente dans back/src/api_fastapi/opportunity/router.py
- 2026-05-18 | quote/invoice | /api/quote/{id}/invoice | decision=migrer | endpoint implemente dans back/src/api_fastapi/quote/router.py
- 2026-05-18 | quote/invoice | /api/invoice/{id}/pdf | decision=migrer | endpoint implemente dans back/src/api_fastapi/quote/router.py
- 2026-05-18 | quote/invoice | /api/invoice/{id}/send | decision=migrer | endpoint implemente dans back/src/api_fastapi/quote/router.py
- 2026-05-18 | quote | /api/quote/{opportunity_id}/generate | decision=migrer | endpoint implemente dans back/src/api_fastapi/quote/router.py
- 2026-05-18 | contact/doc | /api/document/extract-rfp | decision=migrer | endpoint implemente dans back/src/api_fastapi/document/router.py
- 2026-05-18 | contact/doc | /api/document/update-content | decision=migrer | endpoint implemente dans back/src/api_fastapi/document/router.py
- 2026-05-18 | contact/doc | /api/document/{id} | decision=migrer | endpoint implemente dans back/src/api_fastapi/document/router.py
- 2026-05-18 | contact/doc | /api/chat/attachments | decision=migrer | endpoint implemente dans back/src/api_fastapi/document/router.py
- 2026-05-18 | product | /api/products | decision=migrer | endpoint implemente dans back/src/api_fastapi/product/router.py
- 2026-05-18 | product | /api/products/{id} | decision=migrer | endpoint implemente dans back/src/api_fastapi/product/router.py
- 2026-05-18 | legacy-http | opportunity/document GET/POST legacy | decision=supprimer | dispatch legacy reduit a DELETE-only apres migration FastAPI
- 2026-05-18 | legacy-http | quote/opportunity/document route wrappers | decision=supprimer | suppression des wrappers routes.py, matching DELETE centralise dans server_delete_dispatch
- 2026-05-18 | legacy-http | email classify/resync/delete/attachment-download | decision=supprimer | endpoints exposes en FastAPI, dispatch email retire des dispatchers legacy
- 2026-05-18 | legacy-http | google oauth callback path | decision=supprimer | callback oauth unifie sur /api/gmail/oauth/callback, hook /api/google/oauth/callback retire
- 2026-05-18 | legacy-http | get mail dispatch stage | decision=supprimer | suppression de dispatch_get_mail_routes (no-op) du flux GET legacy
- 2026-05-18 | legacy-http | post domain dispatch stage | decision=supprimer | suppression de dispatch_post_domain_routes et du branchement entity au niveau dispatcher
- 2026-05-18 | legacy-http | head/patch no-op dispatchers | decision=supprimer | 404 gere directement dans src.api.server, modules de dispatch no-op retires

## criteres de done pour ce refactor.2

1. chaque ligne HTTP de l'inventaire est en etat `migre`
2. chaque endpoint `legacy` est migre vers FastAPI avec tests associes
3. chaque endpoint `unknown` est implemente et utilise via FastAPI
4. suppression finale du code legacy HTTP non utilise apres verification de parite
5. ouvrir ensuite un plan dedie pour `supabase-direct`
