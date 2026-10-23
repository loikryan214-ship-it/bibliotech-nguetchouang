# BiblioTech

Projet fil rouge du module **Clean Code et Qualité logicielle** (Master 1).
Groupe : NGUETCHOUANG NANSI Ryan · BIEGAIN Arol ([@Arol14](https://github.com/Arol14)) · Lewis ([@Lewis823](https://github.com/Lewis823)).

En trois jours, nous avons transformé une application qui fonctionnait mais se lisait mal en un code lisible, testé et mesuré, **sans changer son comportement** : les 21 tests de caractérisation fournis sont verts à chaque commit, du premier au dernier.

| | Départ (`v0-initial`) | Fin TP 1 | Fin TP 2 (`v2-fin-j2`) | Fin TP 3 (`qualite`) |
| --- | --- | --- | --- | --- |
| Avertissements Ruff (E, W, F, B, S, C90, SIM) | 52 | 0 | 0 | 0 |
| Complexité moyenne (radon) | B (8,29) | A (2,32) | A (2,21) | A (2,16) |
| Pire fonction (radon) | `do_stuff` D (23) | `borrow_refusal` B (6) | `refusal_reason` B (6) | `Library.load` A (5) |
| Tests verts | 21 | 21 | 74 | 104 |

Le détail de chaque étape, avec les commandes Git qui permettent de le vérifier, est dans la partie [5.1](#51-évolution-mesurée-sur-les-trois-tp).

## 1. Présentation

### Contexte

BiblioTech est une application en ligne de commande de gestion d'une bibliothèque municipale. Elle avait été écrite à la hâte (« stagiaire 2019 ») puis modifiée par plusieurs personnes : un seul fichier de 442 lignes, des noms obscurs, un calcul copié quatre fois et un `eval` sur des données lues dans un CSV.

### Fonctionnalités

| Commande | Rôle |
| --- | --- |
| `list` | catalogue et nombre d'exemplaires disponibles |
| `members` | membres et emprunts en cours |
| `borrow <membre> <document>` | emprunter, avec les règles de refus |
| `return <emprunt>` | rendre, avec calcul de la pénalité de retard |
| `overdue` | retards, pénalités et rappels par e-mail (simulés) |
| `report` | rapport d'activité |
| `export <fichier.csv>` | export des emprunts |

L'option `--today AAAA-MM-JJ` simule une autre date du jour.

### Règles métier

| Règle | Valeur |
| --- | --- |
| Durée d'emprunt | livre 21 jours, DVD 7 jours, magazine 3 jours (type inconnu : 21) |
| Emprunts simultanés maximum | standard 3, étudiant 5, premium 8 (type inconnu : 3) |
| Pénalité par jour de retard | livre 0,50 €, DVD 1,00 €, magazine 0,20 € (type inconnu : 0,50 €) |
| Réduction sur les pénalités | étudiant 50 %, premium 100 % |
| Plafond de la pénalité | prix du document |

Un emprunt est refusé si le membre est inactif, s'il a un emprunt en retard, s'il a atteint sa limite, s'il a déjà ce document, ou s'il ne reste aucun exemplaire (dans cet ordre).

### Organisation des fichiers

```
bibliotech.py        point d'entrée : bibliothèque (Library), stockage CSV, commandes
models.py            dataclasses Member, Book, Loan, LateFee, OverdueLoan
rules.py             règles métier pures : loan_days, loan_limit, late_fee
data/                données de l'application (books, members, loans en CSV)
tests/
  test_caracterisation.py + golden/   21 tests fournis (non modifiés)
  conftest.py        fixture library : copie de tests/data/, date figée au 21/10/2026
  data/              jeu de données dédié aux tests unitaires
  test_*.py          83 tests unitaires
SYNTHESE_TP1.md      tableau détaillé des corrections du TP 1
.github/workflows/qualite.yml   contrôle Ruff + pytest à chaque push (bonus)
.pre-commit-config.yaml         Ruff avant chaque commit (bonus)
```

## 2. TP 1 – Clean Code

Branche `tp1/nettoyage`, [pull request #1](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/pull/1), 17 commits. Le détail des 22 corrections est dans [`SYNTHESE_TP1.md`](SYNTHESE_TP1.md).

**Problèmes identifiés** : faille de sécurité (`eval`), `except:` nu, calcul de pénalité copié 4 fois, nombres magiques, noms obscurs (`b`, `m`, `l`, `find(t, id)`, `do_stuff`, `ret`), 7 niveaux de `if` imbriqués, code mort (système de plugins jamais appelé).

**Exemple 1 : sécurité.** Le prix d'un livre était lu avec `eval(x[4])` : une ligne de CSV piégée pouvait exécuter du code. Remplacé par `float(x[4])` ([fc6b789](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/fc6b789)).

**Exemple 2 : duplication (DRY).** Le calcul de pénalité était recopié dans `ret`, `overdue`, `report` et `export` : changer un tarif obligeait à modifier quatre endroits. Il est devenu une seule fonction alimentée par des tables nommées ([5d8e519](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/5d8e519), [86fe9a6](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/86fe9a6)) :

```python
DAILY_FEE = {"book": 0.5, "dvd": 1.0, "magazine": 0.2}
FEE_RATE = {"student": 0.5, "premium": 0}
```

**Exemple 3 : clauses de garde.** `do_stuff` (complexité 23) enchaînait 7 `if` imbriqués avec le message d'erreur loin de sa condition. Renommée `borrow`, avec les règles de refus sorties une par une avec `return` ([291a0ae](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/291a0ae)).

**Résultat** : Ruff 55 → 0 (règles du TP 1), `do_stuff` D (23) → `borrow` A (4), `report` D (21) → A (1).

## 3. TP 2 – Refactoring

Branche `tp2/refactoring`, [pull request #2](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/pull/2), 22 commits, relue en revue croisée puis par l'enseignant.

**Méthode : le test avant le code.** Chaque modification commence par un test unitaire (rouge), puis le code qui le rend vert, puis un commit qui nomme le refactoring (« Extract Function », « Rename Function », « Split Phase »…).

**Restructuration et justification des choix**

- **`late_fee` devient une fonction pure** `late_fee(days_late, kind, member_type, price)` : elle ne dépend plus des dictionnaires de la bibliothèque, on peut donc la tester avec des valeurs calculées à la main.
- **L'emprunt suit la structure du guide** : `borrow` → `refusal_reason` → `has_overdue_loan`, `is_borrowing`, `create_loan`. `create_loan` renvoie l'emprunt sans rien afficher (séparation calcul / affichage, demandée en revue).
- **Split Phase sur les retards** : `find_overdue_loans()` renvoie des `OverdueLoan` sans afficher, ce qui permet de vérifier qu'au 21/10/2026 les retards sont L003, L004, L005, L007 (7,50 / 6,50 / 0,00 / 0,30 €).
- **Move Function** : les règles métier vivent dans `rules.py`.
- **Dataclasses** `Book`, `Member`, `Loan` avec `from_row` / `to_row`, et `LateFee(days, fee)` au lieu d'un tuple lu par index.

**Tests ajoutés (53)** : règles de pénalité (dont l'arrondi vérifié avec `==` et non `pytest.approx`, qui accepterait 0.30000000000000004), emprunts (les 5 motifs de refus, limites 3 / 5 / 8, durées, identifiants inconnus), dates, recherche par identifiant, retards, dataclasses (aller-retour `from_row` / `to_row`), et isolation : `test_isolation.py` prouve que les tests n'écrivent jamais dans `data/`.

## 4. TP 3 – Qualité

Branche `qualite`, partie de l'étiquette `v2-fin-j2` (état validé à la fin du TP 2).

### 4.1 Analyse initiale

Mesures relevées sur `v2-fin-j2` avec les commandes du guide :

```bash
ruff check . --select E,W,F,B,S,C90,SIM --extend-exclude tests --statistics   # 0 avertissement
radon cc -s -a --exclude "tests/*" .     # moyenne A (2,21), pire : refusal_reason B (6)
radon cc -s -n C --exclude "tests/*" .   # aucune fonction en C ou pire
pytest -q                                # 74 passed
```

Ruff et radon ne signalent plus rien de grave après les TP 1 et 2. Nous avons donc complété les mesures par une lecture du code, des essais de la ligne de commande, l'indice de maintenabilité (`radon mi`) et la couverture des tests :

| Défaut | Où et comment repéré | Catégorie | Priorité |
| --- | --- | --- | --- |
| `--today` sans date ou avec une date invalide fait planter l'appli (traceback `IndexError` / `ValueError`) | essai `python bibliotech.py list --today` | Fiabilité | 1 |
| Emprunt pointant vers un livre ou un membre supprimé : `AttributeError` dans `report`, `export`, `overdue` | lecture du code (`find_book` peut renvoyer `None`) | Fiabilité | 1 (dette, voir 4.4) |
| `refusal_reason`, pire fonction du projet | `radon cc`, B (6) | Complexité | 2 |
| `X.get(type, DEFAULT_X)` répété dans `bibliotech.py` pour la durée et la limite : les règles métier débordent de `rules.py` | lecture du code | Duplication | 3 |
| Format monétaire `f"{montant:.2f} EUR"` copié 5 fois | recherche de `EUR` | Duplication | 3 |
| `bibliotech.py` : 524 lignes et 4 responsabilités (modèles, stockage, règles d'emprunt, CLI) | `radon mi` : 19,76, à la limite de la note A (≥ 20) | Maintenabilité | 4 |
| Commandes, retour, rapport et export sans test unitaire (couverts seulement par les tests de caractérisation) | `pytest --cov` : 62 % de `bibliotech.py` | Tests | 4 |
| Règles Ruff du projet sans la famille `S` (sécurité) | `pyproject.toml` | Conventions | 4 |
| Date du jour (`TODAY`) et mode debug en variables globales modifiées par `main` | lecture du code | Maintenabilité | dette (voir 4.4) |

### 4.2 Améliorations réalisées

Une amélioration par commit, `pytest` vert avant et après chacune :

| Commit | Amélioration | Pourquoi |
| --- | --- | --- |
| [927b707](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/927b707) | `--today` invalide affiche `Erreur : --today attend une date au format AAAA-MM-JJ` et renvoie le code 1 | Un utilisateur qui se trompe d'option ne doit pas voir un traceback Python. Les cas valides ne changent pas (tests de caractérisation verts). Tests écrits d'abord : `test_cli.py` |
| [91668bb](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/91668bb) | `refusal_reason` (B 6) découpée en `member_refusal` (A 4) et `book_refusal` (A 3) | Deux responsabilités séparées ; l'ordre des vérifications, donc le message affiché, est conservé et vérifié par `test_borrow.py` |
| [0549c40](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/0549c40) | `rules.loan_days(kind)` et `rules.loan_limit(member_type)` | Toutes les règles métier au même endroit ; cas limites testés (type inconnu, type vide) |
| [4a2da51](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/4a2da51) | `format_eur(montant)` remplace 5 copies du format | Un seul endroit à changer si l'affichage des montants évolue |
| [8e52e72](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/8e52e72) | Les dataclasses passent dans `models.py` | Une responsabilité par module ; indice de maintenabilité de `bibliotech.py` : 19,76 → 25,87 |
| [38c3975](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/38c3975) | Règles Ruff du projet fixées dans `pyproject.toml` (niveau 2) | `ruff check .` applique maintenant les familles du guide, dont `S` ; `S101` (assert) ignoré dans les tests ; `S603` ignoré dans `test_caracterisation.py`, fichier fourni non modifiable, avec la justification en commentaire |
| [4087127](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/4087127) | 13 tests unitaires : retour (pénalité, erreurs), rapport, rappels, export, commandes CLI et codes de sortie | Couverture de `bibliotech.py` : 62 % → 94 % |

Exemple, la règle la plus complexe avant / après :

```python
# Avant : B (6), cinq règles de natures différentes dans une seule fonction
def refusal_reason(self, member, book):
    if not member.active:
        return "membre inactif"
    if self.has_overdue_loan(member.id):
        return "emprunts en retard"
    ...  # puis la limite, le document déjà emprunté, les exemplaires


# Après : A (2), l'ordre membre puis document se lit directement
def refusal_reason(self, member, book):
    return self.member_refusal(member) or self.book_refusal(member, book)
```

### 4.3 Comparaison avant / après

Mesures relancées sur la branche `qualite` avec exactement les mêmes commandes :

| Indicateur | Avant (`v2-fin-j2`) | Après (`qualite`) |
| --- | --- | --- |
| Avertissements Ruff (`--select E,W,F,B,S,C90,SIM`, hors tests) | 0 | 0 |
| Complexité moyenne (radon) | A (2,21) | A (2,16) |
| Pire fonction (nom et note radon) | `Library.refusal_reason` B (6) | `Library.load` A (5) |
| Fonctions notées C ou pire | 0 | 0 |
| Nombre de tests (tous verts) | 74 | 104 |
| Indice de maintenabilité (`radon mi`) | `bibliotech.py` A (19,76), `rules.py` A (90,61) | `bibliotech.py` A (25,87), `models.py` A (65,72), `rules.py` A (87,16) |
| Couverture des tests unitaires (`pytest --cov`, branches) | 63 % | 95 % |

**Commentaire.**

- **Ruff ne bouge pas (0 → 0)** : le nettoyage a été fait au TP 1 (55 → 0). La mesure reste utile comme garde-fou : elle prouve que nos changements n'ont réintroduit aucun avertissement, même avec la famille `S` (sécurité) que le TP 1 ne contrôlait pas.
- **La complexité moyenne baisse peu (2,21 → 2,16)** car elle était déjà en A. Le gain est sur le haut de l'échelle : plus aucune fonction en B, la pire est `Library.load` (A 5), qui charge trois fichiers et gère le mode debug.
- **L'indice de maintenabilité de `bibliotech.py` remonte de 19,76 à 25,87** : il était juste au-dessus de la limite B. Sortir les modèles a réduit le fichier de 524 à 449 lignes.
- **Les tests passent de 74 à 104** et la couverture de 63 % à 95 %. Les lignes restantes non couvertes sont le mode `--debug`, les fonctions `cmd_*` d'une ligne déjà exercées par les tests de caractérisation, et le bloc `if __name__ == "__main__"`.
- **Ce qui n'est pas mesuré mais a changé** : un cas de plantage en moins (`--today`), et un seul endroit pour chaque règle métier et pour le format des montants.

### 4.4 Comparaison avec Git

Commandes de l'étape 4.2 du guide, sur la branche `qualite` :

```bash
git log --oneline v2-fin-j2..qualite     # les commits du TP 3
git diff --stat v2-fin-j2..qualite       # les fichiers modifiés
```

**Commits du TP 3** (du plus ancien au plus récent, chacun avec `pytest` vert), plus le commit qui ajoute cette comparaison au README :

| Commit | Type | Ce qui change |
| --- | --- | --- |
| [927b707](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/927b707) | `fix(fiabilite)` | `--today` sans date ou avec une date invalide affiche une erreur d'usage au lieu d'un traceback |
| [91668bb](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/91668bb) | `refactor(complexite)` | `refusal_reason` (B 6) découpée en `member_refusal` et `book_refusal` |
| [0549c40](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/0549c40) | `refactor(duplication)` | durée et limite d'emprunt dans `rules.loan_days` et `rules.loan_limit` |
| [4a2da51](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/4a2da51) | `refactor(duplication)` | `format_eur` remplace les 5 copies du format des montants |
| [8e52e72](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/8e52e72) | `refactor(maintenabilite)` | dataclasses déplacées dans `models.py` |
| [38c3975](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/38c3975) | `chore(ruff)` | règles Ruff du projet fixées dans `pyproject.toml` |
| [4087127](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/4087127) | `test(couverture)` | tests du retour, du rapport, de l'export, des rappels et des commandes |
| [b07c368](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/b07c368) | `docs` | README final des TP 1 à 3 |
| [bc816ba](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/bc816ba) | `chore(qualite)` | hook pre-commit Ruff |
| [c504825](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/c504825) | `ci` | action GitHub `ruff check` + `pytest` |
| [efcb599](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/commit/efcb599) | `docs(readme)` | précision des bonus dans le README |

**Fichiers modifiés** (`git diff --stat v2-fin-j2..qualite`, avant ce dernier commit de documentation) :

```
 .github/workflows/qualite.yml |  17 +++
 .pre-commit-config.yaml       |   6 +
 README.md                     | 265 +++++++++++++++++++++++++++++++++++-------
 bibliotech.py                 | 157 +++++++------------------
 models.py                     | 104 +++++++++++++++++
 pyproject.toml                |  10 +-
 rules.py                      |  10 ++
 tests/test_cli.py             |  66 +++++++++++
 tests/test_format.py          |  18 +++
 tests/test_return_report.py   |  63 ++++++++++
 tests/test_rules.py           |  29 ++++-
 11 files changed, 584 insertions(+), 161 deletions(-)
```

**Lecture** : `bibliotech.py` perd plus de lignes qu'il n'en gagne (157 lignes touchées, surtout des suppressions) parce que les modèles partent dans `models.py` (104 lignes) ; `rules.py` gagne les deux règles `loan_days` et `loan_limit`. Les tests ajoutés ou complétés représentent environ 176 lignes dans 4 fichiers. Aucun fichier de `tests/golden/`, `tests/test_caracterisation.py` ou `data/` n'apparaît dans la liste : le comportement de référence n'a pas été touché.

### 4.5 Dette restante

| Dette | Pourquoi elle reste | Ce qu'il faudrait faire |
| --- | --- | --- |
| `TODAY` et `DEBUG` sont des variables globales modifiées par `main` | La fixture fournie par le guide (`monkeypatch.setattr(bibliotech, "TODAY", ...)`) repose sur cette variable | Passer la date à `Library(today=...)` et adapter la fixture |
| Un emprunt qui pointe vers un livre ou un membre supprimé fait planter `report`, `export` et `overdue` | C'est une décision métier : ignorer l'emprunt, l'afficher comme orphelin, ou refuser de démarrer ? Aucun jeu de données actuel ne le provoque | Valider les références dans `Library.load` et afficher un message clair, après accord sur la règle |
| `return` renvoie le code 0 même pour un emprunt inconnu ou déjà rendu | Le corriger change un code de sortie figé dans `tests/golden/`, que nous ne devons pas modifier | Renvoyer `EXIT_REFUSED` dans une évolution validée, avec mise à jour des références |
| `bibliotech.py` mélange encore la classe `Library` (stockage + règles d'emprunt) et la ligne de commande | Déplacer `Library` change le module où les tests patchent `DATA` et `TODAY` | Créer `cli.py` et `storage.py` une fois la date injectée (première ligne de ce tableau) |

### 4.6 Pour aller plus loin

- **Niveau 2** : règles Ruff fixées dans `pyproject.toml` (`ruff check .` sans option est vert), indice de maintenabilité mesuré (`radon mi`), mise en forme vérifiée (`ruff format --check .` : tous les fichiers conformes), règles en dictionnaires, tests paramétrés des cas limites (zéro, négatif, type inconnu).
- **Bonus, action GitHub** : `.github/workflows/qualite.yml` lance `ruff check .` puis `pytest` à chaque push et sur la pull request. Résultat visible dans l'onglet *Actions*.
- **Bonus, hook pre-commit** : `.pre-commit-config.yaml` lance `ruff-check` et `ruff-format` avant chaque commit, qui est refusé si le code n'est pas conforme. Premier passage `pre-commit run --all-files` : les deux contrôles passent sans modification.
- **Bonus, couverture** : `pytest --cov=bibliotech --cov=rules --cov=models --cov-branch --cov-report=term-missing` (95 %, voir 4.3).

## 5. Bilan des trois jours

### 5.1 Évolution mesurée sur les trois TP

Les mêmes commandes que l'étape 2.1 du TP 3 ont été relancées sur l'état final de chaque TP (`v0-initial`, fusion de la PR #1 `aed30d7`, `v2-fin-j2`, `qualite`) :

| Indicateur | Départ | Fin TP 1 | Fin TP 2 | Fin TP 3 |
| --- | --- | --- | --- | --- |
| Avertissements Ruff (E, W, F, B, S, C90, SIM, hors tests) | 52 | 0 | 0 | 0 |
| Complexité moyenne (radon) | B (8,29) | A (2,32) | A (2,21) | A (2,16) |
| Pire fonction | `do_stuff` D (23) | `borrow_refusal` B (6) | `refusal_reason` B (6) | `Library.load` A (5) |
| Fonctions notées C ou pire | 4 (`do_stuff` D 23, `report` D 21, `process` C 16, `overdue` C 13) | 0 | 0 | 0 |
| Indice de maintenabilité de `bibliotech.py` | B (10,13) | A (24,42) | A (19,76) | A (25,87) |
| Tests verts | 21 | 21 | 74 | 104 |
| Lignes de code Python (hors tests) | 442 | 472 | 553 | 592 |

**Ce que montre le tableau**

- **Le TP 1 fait l'essentiel du gain sur les mesures** : Ruff 52 → 0, complexité moyenne 8,29 → 2,32, plus aucune fonction en C ou D. C'est le nettoyage des défauts visibles (`eval`, duplication, `if` imbriqués).
- **Le TP 2 fait l'essentiel du gain sur les tests** : 21 → 74, chaque refactoring étant précédé de son test. L'indice de maintenabilité de `bibliotech.py` baisse (24,42 → 19,76) parce que les dataclasses y ont été ajoutées ; le TP 3 corrige ce point en les déplaçant dans `models.py`.
- **Le TP 3 traite ce que les outils voient mal** : fiabilité de la ligne de commande, duplication résiduelle, découpage en modules, couverture (63 % → 95 %), et automatisation des contrôles.
- **Le nombre de lignes augmente** (442 → 592) : docstrings, types, dataclasses et noms explicites prennent de la place. Un code plus long peut être plus simple, la complexité moyenne ayant été divisée par presque 4.

**Comparer les TP avec Git**

| TP | Pull request | Commandes | Commits | Fichiers modifiés |
| --- | --- | --- | --- | --- |
| TP 1 | [#1](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/pull/1) | `git log --oneline v0-initial..aed30d7`, `git diff --stat v0-initial..aed30d7` | 17 | 2 fichiers, +478 / −400 (`bibliotech.py`, `SYNTHESE_TP1.md`) |
| TP 2 | [#2](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/pull/2) | `git log --oneline aed30d7..v2-fin-j2`, `git diff --stat aed30d7..v2-fin-j2` | 22 | 17 fichiers, +673 / −162 (dont 9 fichiers de tests et 3 CSV de `tests/data/`) |
| TP 3 | [#3](https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain/pull/3) | `git log --oneline v2-fin-j2..qualite`, `git diff --stat v2-fin-j2..qualite` | 11 | 11 fichiers, +584 / −161 (voir 4.4) |
| Total | | `git diff --stat v0-initial..qualite` | 50 | 25 fichiers, +1459 / −447 |

Le TP 1 ne touche qu'au code de l'application, le TP 2 surtout aux tests, le TP 3 à la structure, aux contrôles automatiques et à la documentation.

### 5.2 Ce que nous retenons

**Acquis**

- Les tests de caractérisation sont un filet de sécurité : grâce à eux nous avons renommé, découpé et déplacé presque tout le code sans changer une seule sortie.
- Les petits pas vont plus vite : un refactoring par commit, et quand un test casse on sait exactement pourquoi.
- Mesurer plutôt que ressentir : Ruff, radon et la couverture transforment « c'est plus propre » en chiffres que l'on peut comparer, et montrent aussi leurs limites (Ruff ne voit ni la duplication ni les plantages sur une mauvaise option).
- La revue de code trouve ce que l'auteur ne voit pas : la relecture de l'enseignant nous a montré qu'un test d'arrondi avec `pytest.approx` ne prouvait rien.

**Difficultés rencontrées**

- Résister à l'envie de corriger un comportement jugé faux (code de sortie de `return`) : la règle était de ne pas changer le comportement, nous l'avons noté comme dette.
- Les tests unitaires écrivaient au départ dans une copie de `data/` qui pouvait évoluer : nous avons créé un jeu dédié `tests/data/`.
- Travailler à trois sur une même branche : il faut récupérer le travail des autres (`git pull`) avant chaque push pour éviter les branches divergentes.

**Améliorations possibles** : injecter la date du jour, découper `bibliotech.py` en `cli.py` et `storage.py`, valider les références à la lecture des CSV, puis traiter la dette de la partie 4.5.

## 6. Exécution du projet

Python 3.10 ou plus récent.

```bash
git clone https://github.com/loikryan214-ship-it/bibliotech-nguetchouang-biegain.git
cd bibliotech-nguetchouang-biegain
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

**Lancer l'application**

```bash
python bibliotech.py list
python bibliotech.py overdue --today 2026-10-21
git restore data/                  # après borrow ou return, pour revenir aux données d'origine
```

**Lancer les tests**

```bash
pytest                             # 104 passed
pytest --cov=bibliotech --cov=rules --cov=models --cov-branch --cov-report=term-missing
```

**Vérifier le code**

```bash
ruff check .                                                                  # règles du projet
ruff check . --select E,W,F,B,S,C90,SIM --extend-exclude tests --statistics   # mesure du TP 3
ruff format --check .
radon cc -s -a --exclude "tests/*" .
radon cc -s -n C --exclude "tests/*" .
radon mi -s --exclude "tests/*" .
```

Ne modifiez ni `tests/test_caracterisation.py` ni `tests/golden/` : ils figent le comportement de l'application.
