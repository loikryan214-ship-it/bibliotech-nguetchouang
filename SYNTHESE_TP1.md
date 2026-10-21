# Synthèse TP 1 : nettoyage de BiblioTech

Branche `tp1/nettoyage`, partie de l'étiquette `v0-initial`. Chaque correction a fait l'objet d'un commit séparé, avec `pytest` vert (21 tests) avant chaque commit.

## Bilan chiffré

| Indicateur | Avant (`v0-initial`) | Après |
| --- | --- | --- |
| Tests de caractérisation | 21 verts | 21 verts |
| Problèmes signalés par `ruff check .` | 55 | 0 |
| Complexité cyclomatique maximale | 21 (`report`) | 6 (`borrow_refusal`) |
| Fonctions au-dessus du seuil (8) | 8 | 0 |
| Copies du calcul de pénalité | 4 | 1 |

## Corrections

| Défaut | Emplacement | Correction | Principe |
| --- | --- | --- | --- |
| Import étoilé `from datetime import *` qui masque le module `datetime` ; `import os, sys` sur une ligne | en-tête de `bibliotech.py` | Imports explicites `from datetime import date, datetime, timedelta`, un import par ligne | Lisibilité, explicite plutôt qu'implicite |
| Import `json` inutilisé | en-tête | Supprimé | Code mort |
| Système de plugins jamais appelé (`register_plugin`, `run_plugins`), avec argument par défaut mutable `options={}` et `except: pass` | `Library` | Supprimé | YAGNI, code mort |
| Fonction `old_calc_fee` « à ne plus utiliser », variable globale `cache` inutilisée | module | Supprimées | Code mort |
| `eval()` pour lire un prix depuis un fichier CSV : exécution de code arbitraire | `load()` | `float()` | Sécurité |
| Comparaisons `== None`, `== True`, `== False` ; if/else pour calculer un booléen | `do_stuff`, `ret`, `load`, `get_today`, `process` | `is None`, `is not None`, `if x`, `if not x`, `x[4] == "1"` | Lisibilité, idiomes Python |
| `except:` nu qui avale toutes les erreurs | `load()` (lecture de la pénalité) | `except (ValueError, IndexError)` | Gestion d'erreurs explicite |
| Calcul de pénalité copié 4 fois | `ret`, `overdue`, `report`, `export` | Fonction unique `late_fee(days, book, member)` | DRY |
| Nombres magiques : 21/7/3 jours, 3/5/8 emprunts, 0.5/1.0/0.2 €, réductions 50 %/100 %, top 3, format `"%Y-%m-%d"` répété 9 fois | `do_stuff`, `late_fee`, `report`, partout pour les dates | Constantes nommées `LOAN_DAYS`, `MAX_LOANS`, `DAILY_FEE`, `FEE_RATE`, `TOP_BOOKS_COUNT`, `DATE_FORMAT` (dictionnaires + valeur par défaut au lieu de chaînes if/elif) | Lisibilité, source unique de vérité |
| Lecture de CSV copiée 3 fois, fichiers ouverts sans `with` (non fermés en cas d'erreur) | `load`, `save`, `export` | Fonction `read_csv_rows()`, `with open(..., encoding="utf-8")` partout | DRY, robustesse |
| Noms obscurs : `b`, `m`, `l`, `find(t, id)` avec un code lettre et un paramètre qui masque `id`, `nb`, `dispo`, `do_stuff`, `ret` | `Library` | `books`, `members`, `loans`, `find_book`, `find_member`, `find_loan`, `active_loan_count`, `available_copies`, `borrow`, `return_loan` | Noms révélateurs d'intention |
| Recherche par identifiant copiée 3 fois | `find` | Fonction `find_by_id()` | DRY |
| 7 niveaux de `if` imbriqués (« pyramide »), complexité 20 | `do_stuff` → `borrow` | Clauses de garde ; règles de refus regroupées dans `borrow_refusal()` ; helpers `has_overdue_loan`, `has_open_loan`, `next_loan_id` | Fonctions courtes, une seule responsabilité, retour anticipé |
| Calcul « jours de retard » et test « en retard » répétés | `ret`, `overdue`, `report`, `export`, `do_stuff` | Fonctions `parse_date()`, `days_late()`, `is_overdue()`, `is_returned()`, méthodes `loan_fee()`, `open_loans()`, `overdue_loans()` | DRY, abstraction |
| Calcul et envoi du mail mélangés dans la boucle | `overdue` | Fonction `send_reminder()` | Responsabilité unique |
| `report()` de 75 lignes, complexité 21, variables `data2`, `k`, `kk`, `lst`, `c`, `a` | `report` | Découpé en `print_collection_summary`, `print_loan_summary`, `print_loans_by_kind`, `print_top_books` ; comptages avec `Counter` | Fonctions courtes, noms explicites |
| Concaténations de chaînes interminables (19 lignes > 88 caractères) | partout | f-strings, `";".join(...)`, `ruff format` | Lisibilité, mise en forme cohérente |
| Chaîne de `if/elif` sur le nom de la commande, complexité 16 | `process` | Table `COMMANDS` (nom → arguments requis, usage, fonction) et fonctions `cmd_*` ; codes de sortie nommés `EXIT_OK`, `EXIT_USAGE`, `EXIT_REFUSED` | Ouvert/fermé, nombres magiques |
| Analyse des options `--today` / `--debug` dans le bloc `__main__`, variable `debug` en minuscules | `__main__` | Fonctions `parse_options()` et `main()`, globales `TODAY` et `DEBUG` documentées | Responsabilité unique |
| En-tête obsolète (« stagiaire 2019 ») | haut du fichier | Docstring de module | Commentaires utiles |
| Conversion des lignes CSV en dictionnaires dans `load()` | `load` | Fonctions `parse_book()`, `parse_member()`, `parse_loan()` | Responsabilité unique |

## Pistes pour la suite

- Remplacer les dictionnaires par des `dataclass` (`Book`, `Member`, `Loan`) pour éviter les clés en chaînes.
- Séparer les couches : accès aux données (CSV), règles métier, affichage.
- Injecter la date du jour au lieu d'utiliser la globale `TODAY`, puis ajouter des tests unitaires sur `late_fee()` et `borrow_refusal()`.
