# Plan de refactor routing par domaine

## Objectif

Passer d'une organisation des routes par methode HTTP (GET/POST/PUT/DELETE) a une organisation par domaine metier (`auth`, `email`, `quote`, `action`, etc.), en reutilisant les handlers existants dans `back/src/api/<domaine>/handler.py`.

## Probleme actuel

La navigation est difficile car les routes d'un meme domaine sont eclatees dans plusieurs fichiers:

- `server_get_*_dispatch.py`
- `server_post_*_dispatch.py`
- `server_delete_dispatch.py`
- `server_mutation_dispatch.py`
- `server_head_dispatch.py`

Cela ajoute de l'indirection et augmente le cout de maintenance.

## Cible

Un fichier `routes.py` par domaine qui regroupe toutes ses routes, quel que soit le verbe HTTP.

Exemple cible:

- `back/src/api/auth/routes.py`
- `back/src/api/email/routes.py`
- `back/src/api/quote/routes.py`
- `back/src/api/action/routes.py`
- `back/src/api/opportunity/routes.py`
- `back/src/api/document/routes.py`
- `back/src/api/file/routes.py`
- `back/src/api/product/routes.py`
- `back/src/api/rfq/routes.py`
- `back/src/api/csv/routes.py`
- `back/src/api/entity/routes.py`
- `back/src/api/invoice/routes.py`

Et un orchestrateur leger cote serveur qui appelle les routeurs domaine.

## Contraintes

- Garder la compatibilite des endpoints existants.
- Ne pas changer la logique metier des handlers, seulement le wiring.
- Avancer par petits commits (micro-iterations).
- Mettre a jour les tests associes a chaque lot.

## Strategie de migration

Refactor en 4 lots, chacun independamment validable.

### Lot 1 - Fondation domaine (simple)

Domaines cibles:

- `auth`
- `action`
- `csv`

Travail:

1. Creer `routes.py` dans chaque domaine.
2. Y deplacer uniquement la logique de dispatch (matching path + appel handler).
3. Brancher l'orchestrateur principal sur ces nouveaux routeurs.
4. Supprimer les anciens dispatch methods-specifiques devenus obsoletes.
5. Mettre a jour tests unitaires du routing.

Definition of Done:

- Tous les endpoints auth/action/csv passent.
- Aucune regression lint/typecheck.
- Plus d'import vers anciens dispatch fichiers pour ces domaines.

### Lot 2 - Domaines HTTP mixtes

Domaines cibles:

- `email`
- `quote`
- `invoice`

Travail:

1. Consolider GET/POST/DELETE (et PUT si applicable) dans `routes.py` domaine.
2. Conserver les regex/path semantics existantes.
3. Harmoniser les signatures routeur (ex: `dispatch_<domain>_route(handler, method, parsed, qs)`).
4. Mettre a jour tests de non-regression.

Definition of Done:

- Flows email/quote/invoice inchanges fonctionnellement.
- Stack trace de dispatch simplifiee.

### Lot 3 - Domaines complexes

Domaines cibles:

- `opportunity`
- `document`
- `rfq`
- `entity`
- `product`
- `file`

Travail:

1. Deplacer les routes complexes (regex/path variables) dans les routeurs domaine.
2. Isoler les routes transverses dans un module `misc` minimal si necessaire.
3. Nettoyer imports inutiles.

Definition of Done:

- Tous les endpoints de ces domaines routes par fichiers domaine.
- Aucun ancien dispatch method-specifique restant pour eux.

### Lot 4 - Orchestrateur final + cleanup

Travail:

1. Simplifier le serveur en un top-level dispatcher domaine.
2. Supprimer les anciens `server_*_dispatch.py` restants.
3. Supprimer les tests des couches supprimees.
4. Ajouter/mettre a jour tests sur la nouvelle structure.

Definition of Done:

- Le routing n'est plus organise par methode HTTP.
- Arborescence routing lisible par domaine.
- Suite de tests verte sur le scope routing.

## Standard de fichier routeur domaine

Chaque `routes.py` expose idealement:

- `dispatch_<domain>_route(handler, method, parsed, qs) -> bool`

Convention:

- Retourne `True` si la route est prise en charge.
- Retourne `False` sinon.
- Aucune logique metier dans le routeur (delegation stricte aux handlers).

## Validation par lot

A minima, apres chaque lot:

1. Verifier erreurs editeur sur fichiers modifies.
2. Lancer les tests unitaires routing du lot.
3. Tester manuellement 2-3 endpoints critiques du lot.
4. Commit atomique avec message explicite.

Exemple de message de commit:

- `refactor routing migrate auth/action/csv to domain routers`

## Tracking d'avancement

- [x] Lot 1 - Fondation domaine (auth/action/csv)
- [x] Lot 2 - Domaines HTTP mixtes (email/quote/invoice)
- [ ] Lot 3 - Domaines complexes (opportunity/document/rfq/entity/product/file)
- [ ] Lot 4 - Orchestrateur final + cleanup

## Journal de decisions

Ajouter ici les decisions importantes prises en cours de migration.

- 2026-05-15: Creation du plan et decoupage en 4 lots.
- 2026-05-15: Lot 1 termine avec creation de `auth/routes.py`, `action/routes.py`, `csv/routes.py`.
- 2026-05-15: Les dispatchers existants ont ete recables pour deleguer vers les routeurs domaine, afin de garder la compatibilite API.
- 2026-05-15: Tests unitaires ajoutes pour les 3 nouveaux routeurs domaine (`9 passed`).
- 2026-05-15: Lot 2 termine avec creation de `email/routes.py`, `quote/routes.py`, `invoice/routes.py` pour le serveur legacy.
- 2026-05-15: Les dispatchers mail/data/business/domain/delete/legacy ont ete recables vers ces routeurs domaine.
- 2026-05-15: Tests unitaires routing Lot 2 passes (`20 passed`).
