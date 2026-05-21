# Button Refactor Plan

## Composant commun

`front/src/components/common/ActionButton.vue`

Props: `to`, `type`, `variant` (primary | danger | danger-outline | neutral | dark), `size` (sm | xs), `disabled`

- Supports `<button>` et `<router-link>` via prop `to`
- Reset natif button géré globalement dans `style.css` (`@layer base`)

---

## Fichiers déjà migrés ✅

- [x] `front/src/components/products/edit.vue` — Submit, Delete, Cancel
- [x] `front/src/components/family/index.vue` — Add, Clear filters, Delete row
- [x] `front/src/components/vendor/index.vue` — New vendor
- [x] `front/src/components/products/FamilyDiscountPage.vue` — Back, Add line, Save

---

## TODO : fichiers à refactorer

### Priorité 1 — Pages avec formulaires d'action

- [x] `front/src/components/vendor/Edit.vue`
   - L59 `<button class="btn btn-primary">` → `<ActionButton variant="primary">`
   - L68 `<button class="btn btn-secondary">` → `<ActionButton variant="neutral">`
   - L71-76 `<button class="btn btn-danger">` → `<ActionButton variant="danger">`

- [x] `front/src/components/products/BrandEditPage.vue`
   - L21 `<button class="...bg-blue-600...">` toggle form → `<ActionButton variant="primary">`
   - L126 `<button type="submit" class="...bg-blue-600...">` → `<ActionButton variant="primary">`
   - L139 `<button type="button" class="...bg-gray-200...">` reset → `<ActionButton variant="neutral">`
   - L155 `<button type="button" class="...bg-blue-600...">` toggle discount filter → `<ActionButton variant="primary/neutral">` dynamique

- [x] `front/src/components/family/show.vue`
   - L17 `<button class="text-sm text-gray-600 hover:text-gray-900">` back → `<ActionButton variant="neutral" size="xs">`

### Priorité 2 — Confirmations / modales d'action

- [x] `front/src/components/opportunity/components/settings/SettingsPage.vue`
   - L39 `<button class="btn btn-danger ml-4">` → `<ActionButton variant="danger">`
   - L66 `<button class="btn btn-secondary">` → `<ActionButton variant="neutral">`
   - L69 `<button class="btn btn-danger">` → `<ActionButton variant="danger">`

- [x] `front/src/components/opportunity/IndexPage.vue`
   - L221 `<button class="btn btn-secondary">` → `<ActionButton variant="neutral">`
   - L224 `<button class="btn btn-danger">` → `<ActionButton variant="danger">`

- [x] `front/src/components/contact/IndexPage.vue`
   - L5 `<button class="btn btn-neutral">` → `<ActionButton variant="neutral">`
   - L8 `<router-link class="btn btn-primary">` → `<ActionButton to="..." variant="primary">`

### Priorité 3 — Pages opportunity (envoi / preview)

- [x] `front/src/components/opportunity/components/send/SendPage.vue`
   - L196 `<button class="btn btn-primary ml-2">` → `<ActionButton variant="primary">`
   - L202 `<button type="submit" class="btn btn-primary">` → `<ActionButton variant="primary">`
   - L205 `<router-link class="btn btn-secondary">` → `<ActionButton to="..." variant="neutral">`

### Hors périmètre (comportement spécialisé, ne pas migrer)

- `products/DetailPage.vue` — boutons de navigation media (prev/next/thumbnail) avec logique visuelle propre
- `opportunity/components/quote/rank.vue` — icônes de tri spécialisées
- `opportunity/components/quote/QuoteTableHead.vue` — colonnes de tableau spécialisées
- `mail/*` — UI mail avec icônes et états complexes
- `opportunity/components/ActionCard.vue` — card-level custom UI
- `chat/ChatPanel.vue` — bouton toggle icône
- `LocaleSwitcher.vue` — toggle langue
- `PdfAnnotator.vue` — contrôles PDF avec zoom custom
- `login/IndexPage.vue` — formulaire de connexion full-width
- `login/ResetPasswordPage.vue` — idem
