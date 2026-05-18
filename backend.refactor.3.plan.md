# Progress map (plan.3)

| Lot | Description                            | Statut      | Commit/Tag                                                                                                                                                                                   |
| --- | -------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| -1  | Renommage packages/tests API           | ✅ Fait     | edb3ce7, 30a1f49                                                                                                                                                                             |
| 0   | Garde-fou supabase-direct (baseline)   | ✅ Fait     | 1238346                                                                                                                                                                                      |
| 1   | Migration du flux profile (auth)       | ✅ Fait     | f0064c1, 352adad, b91e2b0, 08fa2c9                                                                                                                                                           |
| 2   | Migration account/contact/vendor       | ✅ Fait     | 5b3d3bf, 06e25db, edf5468, 8661e6f, 0c1f33b, fb022fd, cf74c8d, ff6129a, 34c9736, dc8f51a, 0b2749d, 5bc7c91, 024954d, 65c6300, [MIG vendor brands, Edit.vue, baseline 38]                     |
| 3   | Migration brand/family/catalogue       | 🔄 En cours | [MIG catalog brands/families + useCmsData products/admin + useBrandFamilyData + BrandEditPage + family/index + family/show + FamilyDiscountPage + useSuggestionSearch + tests + baseline 30] |
| 4   | Migration opportunity/source/documents | 🔄 En cours | [MIG useOpportunitySource + SourcePage + documents list/detail + PreviewPage + Quote.vue + SendPage + PipelinePage + PipelineStageAccepted + tests + baseline 21]                            |
| 5   | Migration invoices/quote read models   | ⏳ À faire  |                                                                                                                                                                                              |
| 6   | Fermeture/realtime                     | ⏳ À faire  |                                                                                                                                                                                              |

# backend.refactor.3.plan

## objectif

Sortir le frontend des acces metier en `supabase-direct` et transferer ces flux vers des endpoints backend explicites.

Prealable execute pour cette phase:

- renommer `back/src/api_fastapi` en `back/src/api`
- renommer les tests `back/tests/**/api_fastapi/**` en `back/tests/**/api/**`
- remplacer les imports `src.api_fastapi.*` par `src.api.*`

Rationale: l'ancien package `src.api` legacy a ete retire. Garder `api_fastapi` introduisait un bruit historique inutile dans le code, les tests et les commandes runtime.

La regle de cette phase est la suivante:

- les lectures/ecritures metier vers les tables `public` ne doivent plus etre faites directement depuis `front/src/**`
- le SDK Supabase cote frontend peut rester autorise uniquement pour:
  - `auth` (session, sign-in, sign-out, reset password, refresh token)
  - `realtime` transitoire, tant qu'un remplacement backend ou SSE/WebSocket n'est pas tranche

## definition du scope

### dans le scope

- `supabase.from(...).select/insert/update/upsert/delete` depuis `front/src/**`
- `supabase.rpc(...)` s'il existe cote frontend
- acces directs aux tables metier: `account`, `vendor`, `brand`, `family`, `product_family`, `product`, `document`, `document_line`, `contact`, `opportunity`, `opportunity_participant`, `email`, `email_attachment`, `profile`, `sent_email`

### hors scope immediat

- remplacement complet de `supabase.auth.*` si on conserve Supabase Auth
- decision finale sur `realtime` si un simple maintien transitoire est acceptable
- rework UX ou refonte des composants frontend hors besoin de migration transport

## regles de lecture

- `mode=supabase-direct`: lecture/ecriture metier directe depuis le frontend
- `mode=fastapi`: flux deja passe par `fetch/apiUrl` vers le package API HTTP principal `back/src/api/**`
- `mode=auth-sdk`: usage frontend du SDK Supabase autorise a ce stade
- `mode=realtime-sdk`: usage frontend du SDK Supabase a trancher mais acceptable provisoirement
- `owner cible`: service/repository/backend owner qui devra prendre la responsabilite du flux

## politique de tests obligatoire

- toute modification de code dans ce plan doit inclure des tests associes si ils manquent (dans le meme commit ou la meme iteration)
- backend: ajouter/mettre a jour des tests unitaires dans `back/tests/unit/**` avec structure miroir du code migre
- frontend: ajouter/mettre a jour des tests sur les clients API (`front/src/api/**`) et la logique des composants/composables impactes
- si un test ne peut pas etre ajoute immediatement, documenter explicitement le risque et ouvrir une tache de rattrapage dans le lot en cours
- chaque iteration doit executer au minimum les tests cibles du flux modifie avant commit

## hypothese de travail

Le plan.2 a termine la sortie du transport HTTP legacy. Le prochain goulot est maintenant le couplage direct du frontend aux tables Supabase. L'objectif du plan.3 n'est pas de supprimer `supabase-js` du frontend a tout prix, mais de supprimer les acces metier directs et de les remplacer par une API backend stable.

Le nommage du package backend a ete normalise sur `src.api`, le suffixe `api_fastapi` ayant ete retire.

## inventaire initial observe

Constat initial: environ `44` points d'entree frontend importent `front/src/lib/supabase.ts`.

### A. auth et session

| surface frontend                                   | type                                                          | mode actuel                                  | decision cible                                                            |
| -------------------------------------------------- | ------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------- |
| `front/src/stores/auth.ts`                         | sign-up / sign-in / sign-out / refresh session / profile sync | `auth-sdk` + `supabase-direct` sur `profile` | conserver `supabase.auth.*`, migrer les operations `profile` vers backend |
| `front/src/router/index.ts`                        | guard session                                                 | `auth-sdk`                                   | conserver provisoirement                                                  |
| `front/src/components/login/ResetPasswordPage.vue` | reset password                                                | `auth-sdk`                                   | conserver provisoirement                                                  |

### B. mail, source et realtime

| surface frontend                                                               | tables / flux                                                                     | mode actuel                                        | owner cible                                      |
| ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------ |
| `front/src/components/mail/IndexPage.vue`                                      | `email_attachment`, realtime, auth session reuse                                  | mix `fastapi` + `supabase-direct` + `realtime-sdk` | backend email/doc + decision specifique realtime |
| `front/src/composables/useOpportunitySource.ts`                                | `opportunity_participant`, `email_attachment`, `document`, `email`, `opportunity` | `fastapi` + storage HTTP                           | routers opportunity/document/email               |
| `front/src/components/opportunity/components/source/SourcePage.ts`             | source opportunity/doc                                                            | `fastapi`                                          | router opportunity/document                      |
| `front/src/components/opportunity/components/documents/DocumentsPage.vue`      | documents                                                                         | mixte                                              | router document                                  |
| `front/src/components/opportunity/components/documents/DocumentDetailPage.vue` | document detail                                                                   | mixte                                              | router document                                  |

### C. account, contact, vendor

| surface frontend                                                      | tables                                                | mode actuel       | owner cible                                                |
| --------------------------------------------------------------------- | ----------------------------------------------------- | ----------------- | ---------------------------------------------------------- |
| `front/src/components/account/IndexPage.vue`                          | `account` list                                        | `supabase-direct` | nouveau router/service account                             |
| `front/src/components/account/Edit.vue`                               | `account` CRUD                                        | `supabase-direct` | nouveau router/service account                             |
| `front/src/components/opportunity/components/account/AccountPage.vue` | `account` lookup dans contexte opportunity            | `supabase-direct` | nouveau router/service account                             |
| `front/src/components/contact/IndexPage.vue`                          | `contact` list                                        | `supabase-direct` | nouveau router/service contact                             |
| `front/src/components/contact/DetailPage.vue`                         | `contact` detail/update                               | `supabase-direct` | nouveau router/service contact                             |
| `front/src/components/vendor/index.vue`                               | `vendor`, `brand`, `family`, `product_family` agreges | `supabase-direct` | etendre router vendor ou creer endpoints agreges catalogue |
| `front/src/components/vendor/Edit.vue`                                | `vendor` CRUD + brand lookup                          | `supabase-direct` | router vendor                                              |

### D. brand, family, product catalogue CMS

| surface frontend                                          | tables                                                   | mode actuel       | owner cible                            |
| --------------------------------------------------------- | -------------------------------------------------------- | ----------------- | -------------------------------------- |
| `front/src/components/products/BrandEditPage.vue`         | `brand`, `family`                                        | `supabase-direct` | nouveau router/service brand           |
| `front/src/components/family/index.vue`                   | `family`, `product`, `product_family`                    | `supabase-direct` | nouveau router/service family          |
| `front/src/components/family/show.vue`                    | `family` detail                                          | `supabase-direct` | router family                          |
| `front/src/components/products/FamilyDiscountPage.vue`    | `family`, `document`, `document_line`                    | `fastapi`         | router family + quote/document service |
| `front/src/components/products/useBrandFamilyData.ts`     | `vendor`, `brand`, `family`, `product_family`, `product` | `fastapi`         | endpoints catalogue de reference       |
| `front/src/components/products/cms/useCmsData.ts`         | `brand`, `family`                                        | `fastapi`         | endpoints catalogue de reference       |
| `front/src/components/admin/components/cms/useCmsData.ts` | `brand`, `family`                                        | `fastapi`         | endpoints catalogue de reference       |
| `front/src/composables/useSuggestionSearch.ts`            | `product` search                                         | `supabase-direct` | etendre router product/search          |
| `front/src/components/products/IndexPage.vue`             | produit/cms                                              | mixte             | router product                         |
| `front/src/components/products/DetailPage.vue`            | produit detail                                           | `supabase-direct` | router product                         |

### E. opportunity, quote, invoice

| surface frontend                                                                                                    | tables / flux                                       | mode actuel                 | owner cible                                                 |
| ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | --------------------------- | ----------------------------------------------------------- |
| `front/src/components/opportunity/IndexPage.vue`                                                                    | opportunity list + enrichissements locaux           | mixte                       | router opportunity                                          |
| `front/src/components/opportunity/OpportunityHeader.vue`                                                            | opportunity header                                  | `supabase-direct` + fastapi | router opportunity                                          |
| `front/src/components/opportunity/components/settings/SettingsPage.vue`                                             | delete/update opportunity                           | mixte                       | router opportunity                                          |
| `front/src/components/opportunity/components/pipeline/PipelinePage.vue`                                             | status/pipeline                                     | `supabase-direct`           | router opportunity                                          |
| `front/src/components/opportunity/components/pipeline/components/StageManager.vue`                                  | pipeline transitions                                | mixte                       | router opportunity/quote                                    |
| `front/src/components/opportunity/components/pipeline/components/PipelineStageRfp/PipelineStageRfp.vue`             | quote/rfq stage                                     | mixte                       | deja partiellement FastAPI, finir la sortie Supabase        |
| `front/src/components/opportunity/components/pipeline/components/PipelineStageAccepted/PipelineStageAccepted.vue`   | quote/invoice stage                                 | mixte                       | router quote                                                |
| `front/src/components/opportunity/components/pipeline/components/PipelineStageInvoiced/PipelineStageInvoiced.vue`   | invoice stage                                       | `supabase-direct`           | router quote/invoice                                        |
| `front/src/components/opportunity/components/pipeline/components/PipelineStagePaid/PipelineStagePaid.vue`           | paid stage                                          | `supabase-direct`           | router quote/invoice                                        |
| `front/src/components/opportunity/components/pipeline/components/PipelineStageClosedWon/PipelineStageClosedWon.vue` | closed-won stage                                    | `supabase-direct`           | router opportunity                                          |
| `front/src/components/opportunity/components/quote/Quote.vue`                                                       | quote/doc access                                    | mixte                       | router quote                                                |
| `front/src/components/opportunity/components/quote/QuoteDocument.vue`                                               | quote document data                                 | `supabase-direct`           | router quote/document                                       |
| `front/src/components/opportunity/components/preview/PreviewPage.vue`                                               | quote preview/doc                                   | mixte                       | router quote/document                                       |
| `front/src/components/opportunity/components/send/SendPage.vue`                                                     | quote send/doc lookup                               | mixte                       | router opportunity/quote                                    |
| `front/src/components/opportunity/components/invoices/InvoicesPage.vue`                                             | invoice list                                        | `supabase-direct`           | router quote/invoice                                        |
| `front/src/components/opportunity/components/invoices/InvoiceDetailPage.vue`                                        | invoice detail + sent email + contacts              | `supabase-direct`           | router quote/invoice/contact                                |
| `front/src/components/invoices/InvoicesPage.vue`                                                                    | invoice list                                        | `supabase-direct`           | router quote/invoice                                        |
| `front/src/components/invoices/InvoiceDetailPage.vue`                                                               | invoice detail + sent email + opportunity + contact | `supabase-direct`           | router quote/invoice/contact                                |
| `front/src/components/opportunity/components/actions/ActionsPage.vue`                                               | action context mixed with auth token                | mixte                       | deja majoritairement FastAPI, verifier le reliquat Supabase |

## priorisation

### lot -1 - renommage de package avant migration metier

1. fait: renommer `back/src/api_fastapi` en `back/src/api`
2. fait: renommer `back/tests/unit/api_fastapi` en `back/tests/unit/api`
3. fait: renommer `back/tests/integration/api_fastapi` en `back/tests/integration/api`
4. fait: remplacer tous les imports `src.api_fastapi.*` par `src.api.*`
5. fait: mettre a jour les commandes runtime et de dev (`src.api_fastapi.server` -> `src.api.server`)
6. fait: valider que la suite API renommee passe avant d'entamer les lots `supabase-direct`

### lot 0 - frontiere et instrumentation

1. fait: geler la creation de nouveaux acces `supabase-direct` metier dans `front/src/**`
2. fait: documenter la regle: `supabase.auth.*` autorise, `supabase.from(...)` metier interdit pour tout nouveau code
3. fait: ajouter une verification outillee via `front/scripts/check-supabase-direct.mjs`
4. fait: figer une baseline dans `front/config/supabase-direct-allowlist.txt` (39 fichiers)
5. fait: exposer la verification via `npm run check:supabase-direct` dans `front/package.json`

### lot 1 - auth/profil et garde de session

1. conserver `supabase.auth.*` pour login/session/reset password
2. sortir `profile` du frontend direct dans `front/src/stores/auth.ts`
3. definir si le profil utilisateur devient un endpoint backend dedie (`/api/me`, `/api/profile`) ou reste derive du token

### lot 2 - account/contact/vendor de base

1. fait: creer `account` list/detail/create/update/delete en FastAPI

- fait: disparition de `supabase.from('account')` dans `front/src/**`
- fait: tests unitaires backend ajoutes pour `account` router et `profile` router (`back/tests/unit/api/account/router/*`, `back/tests/unit/api/profile/router/*`)

2. fait: creer `contact` list/detail/create/update/delete en FastAPI

- fait: tests unitaires backend ajoutes pour `contact` router (`back/tests/unit/api/contact/router/*`)

3. fait: completer `vendor` pour couvrir liste/detail/CRUD et les agregats de comptage (brands/families/products) cote backend

- fait: tests unitaires backend ajoutes pour `vendor` router (`back/tests/unit/api/vendor/router/*`)
- fait: client frontend `front/src/api/vendor.ts` avec tests unitaires (`front/tests/unit/src/api/vendor/*`)

4. fait: migration complète des pages `account/*`, `contact/*`, `vendor/*`

- fait: `front/src/components/account/Edit.vue` -> `front/src/api/account.ts`
- fait: `front/src/components/account/IndexPage.vue` -> `front/src/api/account.ts`
- fait: `front/src/components/opportunity/OpportunityHeader.vue` (create/find account) -> `front/src/api/account.ts`
- fait: `front/src/components/opportunity/components/account/AccountPage.vue` (load/search/create/update account) -> `front/src/api/account.ts`
- fait: `front/src/components/opportunity/components/source/SourcePage.ts` (create/find account) -> `front/src/api/account.ts`
- fait: `front/src/components/contact/DetailPage.vue` (chargement liste account) -> `front/src/api/account.ts`
- fait: `front/src/components/opportunity/IndexPage.vue` (mapping account_id -> account_name) -> `front/src/api/account.ts`
- fait: `front/src/components/opportunity/components/quote/Quote.vue` (chargement account detail) -> `front/src/api/account.ts`
- fait: `front/src/components/contact/IndexPage.vue` (liste contacts) -> `front/src/api/contact.ts`
- fait: `front/src/components/contact/DetailPage.vue` (detail/create/update/delete contact) -> `front/src/api/contact.ts`
- fait: `front/src/components/vendor/index.vue` (liste + compteurs) -> `front/src/api/vendor.ts`
- fait: `front/src/components/vendor/Edit.vue` (detail/create/update/delete vendor + chargement marques associées) -> `front/src/api/vendor.ts`
- fait: extension backend/endpoint pour chargement des brands associés à un vendor
- fait: extension client frontend + tests pour `listVendorBrands`
- fait: migration Edit.vue terminée, plus d'accès direct Supabase
- fait: baseline guardrail réduit à 38 fichiers
- fait: tous les tests backend/frontend et guardrail passent

### lot 3 - brand/family/catalogue

1. en cours: creer endpoints `brand` et `family` manquants

- fait: ajout des endpoints de reference `GET /api/catalog/brands` et `GET /api/catalog/families`
- fait: tests unitaires backend ajoutes (`back/tests/unit/api/catalog/router/test_list_catalog_brands.py`, `back/tests/unit/api/catalog/router/test_list_catalog_families.py`)

2. traiter les operations sur `product_family` via backend

3. en cours: remplacer les composables catalogue partages (`useCmsData`, `useBrandFamilyData`, `useSuggestionSearch`)

- fait: `front/src/components/products/cms/useCmsData.ts` migre vers `front/src/api/catalog.ts`
- fait: `front/src/components/admin/components/cms/useCmsData.ts` migre vers `front/src/api/catalog.ts`
- fait: `front/src/components/products/useBrandFamilyData.ts` migre vers `front/src/api/catalog.ts` + `front/src/api/vendor.ts`
- fait: `front/src/components/products/BrandEditPage.vue` migre vers `front/src/api/brand.ts` + `front/src/api/vendor.ts`
- fait: nouveau client API `front/src/api/catalog.ts`
- fait: nouveau client API `front/src/api/brand.ts`
- fait: tests unitaires frontend ajoutes pour API catalog/brand et composables `useCmsData`/`useBrandFamilyData`
- fait: guardrail supabase-direct valide, baseline reduite a `34` fichiers

4. migrer `BrandEditPage`, `family/index`, `family/show`, `FamilyDiscountPage`

- fait: `front/src/components/family/index.vue` migre vers `front/src/api/family.ts` + `front/src/composables/useSuggestionSearch.ts`
- fait: `front/src/components/family/show.vue` migre vers `front/src/api/family.ts`
- fait: `front/src/components/products/FamilyDiscountPage.vue` migre vers `front/src/api/family.ts` (`/api/family/{id}/discount-lines`)
- fait: `front/src/composables/useSuggestionSearch.ts` migre vers `GET /api/products`
- fait: endpoints backend ajoutes `GET/PUT /api/family/{id}/discount-lines` + tests
- fait: guardrail supabase-direct valide, baseline reduite a `30` fichiers

### lot 4 - opportunity/source/documents restants

1. fait: sortir `useOpportunitySource` du direct DB

- fait: nouvel endpoint backend `GET /api/opportunity/{id}/source`
- fait: nouveau client frontend `front/src/api/opportunitySource.ts`
- fait: `front/src/composables/useOpportunitySource.ts` migre vers API backend
- fait: `front/src/components/opportunity/components/source/SourcePage.ts` migre vers `front/src/api/opportunity.ts`
- fait: tests unitaires backend/frontend ajoutes pour cette API
- fait: guardrail supabase-direct valide, baseline reduite a `28` fichiers

2. fait: migrer `DocumentsPage` et `DocumentDetailPage` hors `supabase.from('document')`

- fait: endpoints backend ajoutes `GET /api/document?opportunity_id=...` et `GET /api/document/{id}?opportunity_id=...`
- fait: nouveau client frontend `front/src/api/document.ts`
- fait: `front/src/components/opportunity/components/documents/DocumentsPage.vue` migre vers API backend pour la liste
- fait: `front/src/components/opportunity/components/documents/DocumentDetailPage.vue` migre vers API backend pour le detail
- fait: tests unitaires backend/frontend ajoutes pour les nouveaux endpoints/clients
- fait: guardrail supabase-direct valide, baseline reduite a `26` fichiers

3. fait: migrer `PreviewPage` hors `supabase.from('document')`

- fait: ajout endpoint backend `PUT /api/document/{id}/storage-key` pour vider `storage_key`
- fait: extension client frontend `front/src/api/document.ts` (`clearDocumentStorageKey`)
- fait: `front/src/components/opportunity/components/preview/PreviewPage.vue` migre vers API backend document
- fait: tests unitaires backend/frontend ajoutes pour cette route/client
- fait: guardrail supabase-direct valide, baseline reduite a `25` fichiers

4. fait: migrer `Quote.vue` hors `supabase.from('opportunity'|'document'|'opportunity_participant'|'contact')`

- fait: enrichissement backend `GET /api/document/{id}` avec `document_line`
- fait: `front/src/components/opportunity/components/quote/Quote.vue` migre vers clients API (`opportunity`, `document`, `contact`, `source`)
- fait: tests unitaires backend/frontend executes sur les routes/clients impactes
- fait: guardrail supabase-direct valide, baseline reduite a `24` fichiers

5. fait: migrer `SendPage.vue` hors `supabase.from('document'|'sent_email'|'opportunity'|'opportunity_participant'|'contact'|'email')`

- fait: ajout endpoint backend `GET /api/opportunity/{id}/sent-email`
- fait: extension client frontend `front/src/api/opportunity.ts` (`getOpportunitySentEmail`)
- fait: `front/src/components/opportunity/components/send/SendPage.vue` migre vers clients API backend (`opportunity`, `opportunitySource`, `document`, `contact`)
- fait: tests unitaires backend/frontend ajoutes pour le nouvel endpoint/client
- fait: guardrail supabase-direct valide, baseline reduite a `23` fichiers

6. fait: migrer `PipelinePage.vue` hors `supabase.from('opportunity'|'contact')`

- fait: `front/src/components/opportunity/components/pipeline/PipelinePage.vue` migre vers clients API backend (`opportunity`, `account`, `contact`)
- fait: tests unitaires frontend executes sur les clients API utilises
- fait: guardrail supabase-direct valide, baseline reduite a `22` fichiers

7. fait: migrer `PipelineStageAccepted.vue` hors `supabase.from('document'|'opportunity')`

- fait: extension client frontend `front/src/api/opportunity.ts` (`advanceOpportunityStage`)
- fait: `front/src/components/opportunity/components/pipeline/components/PipelineStageAccepted/PipelineStageAccepted.vue` migre vers APIs backend `document`/`opportunity`
- fait: tests unitaires frontend ajoutes pour le nouvel helper API
- fait: guardrail supabase-direct valide, baseline reduite a `21` fichiers

8. finir la migration des composants opportunity qui lisent encore `opportunity`, `email`, `participant` en direct
9. centraliser les agregats source/document/participant cote backend

### lot 5 - invoices et quote read models

1. creer read models backend pour `InvoicesPage` et `InvoiceDetailPage`
2. couvrir les jointures `document + sent_email + opportunity + contact` cote backend au lieu du frontend
3. supprimer les lectures directes `document`, `sent_email`, `contact`, `opportunity` dans ces ecrans

### lot 6 - realtime et fermeture

1. trancher si le realtime email reste en `supabase-js` ou passe par une autre couche
2. si conservation transitoire: restreindre explicitement `front/src/lib/supabase.ts` a `auth` + `realtime`
3. verifier qu'il ne reste plus aucun acces direct metier dans `front/src/**`

## decisions deja prises pour ce plan.3

- `2026-05-18 | global | supabase-direct frontend metier | decision=supprimer progressivement | le transport HTTP legacy est retire, le prochain couplage structurel est l'acces direct du frontend aux tables`
- `2026-05-18 | architecture | renommage src.api_fastapi -> src.api | decision=fait | le package legacy src.api n'existe plus, le suffixe fastapi etait devenu un nom de transition inutile`
- `2026-05-18 | auth | supabase.auth.* | decision=conserver provisoirement | sortir du flux supabase-direct ne signifie pas forcement remplacer Supabase Auth dans cette phase`
- `2026-05-18 | data metier | supabase.from(... ) dans front/src/** | decision=migrer vers backend | objectif central du plan.3`
- `2026-05-18 | realtime | subscriptions email | decision=a trancher | peut rester provisoirement si le reste du metier sort du direct DB`
- `2026-05-18 | lot 0 | guardrail supabase-direct | decision=actif | toute nouvelle surface frontend utilisant supabase direct hors allowlist echoue via npm run check:supabase-direct`
- `2026-05-18 | lot 3 | catalogue refs (brand/family) + composables CMS | decision=en cours | endpoints /api/catalog/* actifs, useCmsData/useBrandFamilyData/BrandEditPage/family/index/family/show/FamilyDiscountPage/useSuggestionSearch migres, baseline guardrail 30`
- `2026-05-18 | lot 4 | source opportunity | decision=en cours | useOpportunitySource + SourcePage migres vers /api/opportunity/{id}/source et /api/opportunity/{id}/name, baseline guardrail 28`

## criteres de done pour ce refactor.3

1. aucun composant/frontend composable ne fait de lecture/ecriture metier directe via `supabase.from(...)`
2. les jointures et agregats metier sont servis par des endpoints backend explicites
3. `front/src/lib/supabase.ts` n'est plus utilise que pour `auth` et, si valide, `realtime`
4. chaque comportement migre ou modifie a des tests associes (obligatoire, pas optionnel)
5. un grep repo confirme la disparition des acces frontend directs aux tables metier
