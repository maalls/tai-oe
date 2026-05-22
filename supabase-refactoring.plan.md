# Plan de refactor Supabase vers SQL/Postgres

## Objectif

Supprimer les flux d'acces directs a Supabase dans les repositories metier et faire converger tout l'acces aux donnees vers le flux SQL/Postgres deja centralise autour de `DatabaseService` et `DatabaseHandler`.

Le but n'est pas de changer la base cible, mais de n'avoir qu'un seul chemin technique d'acces aux donnees.

## Etat actuel

- Les repositories metier utilisent encore `get_supabase_service()` directement pour lire et ecrire.
- La pile `DatabaseRepository` / `DatabaseHandler` existe deja et utilise la connexion Postgres injectee.
- `EmailRepository` sert deja de facade metier, mais delegate encore a un adapter Supabase pour certaines operations.

## Principe cible

1. Les services et controllers continuent a parler a des repositories metier.
2. Les repositories metier deleguent a des adapters d'infrastructure injectes.
3. Les adapters d'infrastructure utilisent uniquement la connexion Postgres centrale.
4. Supabase ne reste qu'un detail d'implementation eventuel pour des usages vraiment specifiques, pas comme voie standard des repositories.

## Contraintes

- Conserver la compatibilite fonctionnelle des endpoints et des commandes.
- Faire la migration par petits lots validables.
- Ne pas recréer un deuxieme canal d'acces aux donnees dans un nouveau module.
- Mettre a jour les tests a chaque lot quand le comportement change.

## Strategie de migration

### Lot 1 - Inventaire et frontieres

Travail:

1. Lister tous les repositories qui utilisent encore Supabase direct.
2. Lister les repositories qui passent deja par `DatabaseHandler`.
3. Identifier les operations qui sont purement CRUD SQL et celles qui portent de la logique metier.
4. Decider pour chaque module si la logique doit rester dans `EmailRepository` / `OpportunityRepository` ou basculer dans un adapter infra.

Definition of Done:

- Cartographie complete des flux Supabase et Postgres.
- Liste des modules a migrer en priorite.

### Lot 2 - Extraction des adapters infra

Travail:

1. Deplacer les operations techniques de persistence hors des repositories metier.
2. Injecter une dependance DB commune dans les adapters.
3. Faire de `EmailRepository` une vraie facade metier, sans acces direct a Supabase.
4. Conserver temporairement des wrappers de compatibilite si necessaire.

Definition of Done:

- Les repositories metier ne parlent plus directement a Supabase pour les operations visees.
- Les tests unitaires ciblant ces flux passent.

### Lot 3 - Migration des repositories restants

Travail:

1. Migrer `ActionRepository`, `OpportunityRepository`, `GmailProviderRepository`, `OAuthTokenRepository` et les autres modules encore sur Supabase direct.
2. Basculer les appels de lecture/ecriture vers les primitives SQL centralisees.
3. Uniformiser les conventions de nommage et de construction des requetes.

Definition of Done:

- Plus de repository metier standard ne depend de `get_supabase_service()` pour l'acces aux donnees.
- Les flux de lecture et d'ecriture passent tous par la meme couche technique.

### Lot 4 - Nettoyage final

Travail:

1. Supprimer les helpers devenus inutiles.
2. Retirer les imports Supabase restants des modules migrés.
3. Revoir les tests pour refleter le nouveau point d'entree unique.
4. Documenter la regle de couche dans le runbook backend.

Definition of Done:

- Un seul chemin technique d'acces aux donnees reste en usage normal.
- La documentation de l'architecture est a jour.

## Reperes de validation

Apres chaque lot:

1. Lancer les tests cibles du lot.
2. Lancer la suite backend si le lot touche un flux transversal.
3. Verifier les imports et les erreurs d'analyse du fichier modifie.
4. Faire un commit atomique avec un message descriptif.

## Journal de decisions

- 2026-05-22: Decision prise de converger vers un seul flux SQL/Postgres pour l'acces aux donnees.
- 2026-05-22: Le repository metier reste la facade de domaine; les details de persistence doivent vivre dans l'infrastructure.
- 2026-05-22: La migration doit se faire sans recréer une deuxieme voie d'acces aux donnees.