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
| `front/src/composables/useOpportunitySource.ts`                                | `opportunity_participant`, `email_attachment`, `document`, `email`, `opportunity` | `supabase-direct` + storage HTTP                   | routers opportunity/document/email               |
| `front/src/components/opportunity/components/source/SourcePage.ts`             | source opportunity/doc                                                            | mixte                                              | router opportunity/document                      |
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

| surface frontend                                          | tables                                | mode actuel       | owner cible                            |
| --------------------------------------------------------- | ------------------------------------- | ----------------- | -------------------------------------- |
| `front/src/components/products/BrandEditPage.vue`         | `brand`, `family`                     | `supabase-direct` | nouveau router/service brand           |
| `front/src/components/family/index.vue`                   | `family`, `product`, `product_family` | `supabase-direct` | nouveau router/service family          |
| `front/src/components/family/show.vue`                    | `family` detail                       | `supabase-direct` | router family                          |
| `front/src/components/products/FamilyDiscountPage.vue`    | `family`, `document`, `document_line` | `supabase-direct` | router family + quote/document service |
| `front/src/components/products/useBrandFamilyData.ts`     | `vendor`, `brand`                     | `supabase-direct` | endpoints catalogue de reference       |
| `front/src/components/products/cms/useCmsData.ts`         | `brand`, `family`                     | `supabase-direct` | endpoints catalogue de reference       |
| `front/src/components/admin/components/cms/useCmsData.ts` | `brand`, `family`                     | `supabase-direct` | endpoints catalogue de reference       |
| `front/src/composables/useSuggestionSearch.ts`            | `product` search                      | `supabase-direct` | etendre router product/search          |
| `front/src/components/products/IndexPage.vue`             | produit/cms                           | mixte             | router product                         |
| `front/src/components/products/DetailPage.vue`            | produit detail                        | `supabase-direct` | router product                         |

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

1. geler la creation de nouveaux acces `supabase-direct` metier dans `front/src/**`
2. documenter la regle: `supabase.auth.*` autorise, `supabase.from(...)` metier interdit pour tout nouveau code
3. ajouter, si utile, une verification simple CI ou grep cible qui remonte les nouveaux imports/queries directes

### lot 1 - auth/profil et garde de session

1. conserver `supabase.auth.*` pour login/session/reset password
2. sortir `profile` du frontend direct dans `front/src/stores/auth.ts`
3. definir si le profil utilisateur devient un endpoint backend dedie (`/api/me`, `/api/profile`) ou reste derive du token

### lot 2 - account/contact/vendor de base

1. creer `account` list/detail/create/update/delete en FastAPI
2. creer `contact` list/detail/update en FastAPI
3. completer `vendor` pour couvrir liste/detail/CRUD et les agregats actuellement reconstruits cote frontend
4. migrer les pages `account/*`, `contact/*`, `vendor/*`

### lot 3 - brand/family/catalogue

1. creer endpoints `brand` et `family` manquants
2. traiter les operations sur `product_family` via backend
3. remplacer les composables catalogue partages (`useCmsData`, `useBrandFamilyData`, `useSuggestionSearch`)
4. migrer `BrandEditPage`, `family/index`, `family/show`, `FamilyDiscountPage`

### lot 4 - opportunity/source/documents restants

1. sortir `useOpportunitySource` du direct DB
2. finir la migration des composants opportunity qui lisent encore `opportunity`, `document`, `email`, `participant` en direct
3. centraliser les agregats source/document/participant cote backend

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

## criteres de done pour ce refactor.3

1. aucun composant/frontend composable ne fait de lecture/ecriture metier directe via `supabase.from(...)`
2. les jointures et agregats metier sont servis par des endpoints backend explicites
3. `front/src/lib/supabase.ts` n'est plus utilise que pour `auth` et, si valide, `realtime`
4. les composants migrés ont des tests associes quand un comportement vivant backend est introduit ou modifie
5. un grep repo confirme la disparition des acces frontend directs aux tables metier
