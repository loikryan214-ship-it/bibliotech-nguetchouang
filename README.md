# BiblioTech

Application en ligne de commande de gestion d'une bibliothèque municipale : catalogue, membres, emprunts, retours, pénalités de retard, rappels et rapports.

L'application **fonctionne**, mais son code a été écrit à la hâte et modifié par de nombreuses personnes. C'est le projet fil rouge du module *Clean Code et Qualité logicielle* : vous allez l'améliorer pendant trois jours **sans changer son comportement**.

## Installation

Python 3.10 ou plus récent est nécessaire.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Utilisation

```bash
python bibliotech.py list                    # catalogue et disponibilités
python bibliotech.py members                 # membres et emprunts en cours
python bibliotech.py borrow M005 B005        # emprunter un document
python bibliotech.py return L004             # rendre un document
python bibliotech.py overdue                 # retards et envoi des rappels
python bibliotech.py report                  # rapport d'activité
python bibliotech.py export emprunts.csv     # export des emprunts
```

L'option `--today AAAA-MM-JJ` permet de simuler une autre date, par exemple :

```bash
python bibliotech.py overdue --today 2026-10-21
```

Les données se trouvent dans le dossier `data/`. Les commandes `borrow` et `return` modifient `data/loans.csv` : pour revenir aux données d'origine, lancez `git restore data/`.

## Règles métier

| Règle | Valeur |
| --- | --- |
| Durée d'emprunt | livre 21 jours, DVD 7 jours, magazine 3 jours |
| Emprunts simultanés maximum | standard 3, étudiant 5, premium 8 |
| Pénalité par jour de retard | livre 0,50 €, DVD 1,00 €, magazine 0,20 € |
| Réduction sur les pénalités | étudiant 50 %, premium 100 % |
| Plafond de la pénalité | prix du document |

Un emprunt est refusé si le membre est inactif, s'il a un emprunt en retard, s'il a atteint sa limite, s'il a déjà ce document, ou s'il ne reste aucun exemplaire.

## Tests

```bash
pytest
```

Le dossier `tests/` contient des **tests de caractérisation** : ils lancent l'application et comparent sa sortie à des résultats de référence. Ils ne dépendent pas de l'organisation interne du code. Vous pouvez donc renommer, découper et déplacer librement le code de `bibliotech.py` : **tant que les tests restent verts, le comportement est préservé.**

Ne modifiez pas `tests/test_caracterisation.py` ni le dossier `tests/golden/`.

## Analyse statique

```bash
ruff check .            # signaler les problèmes
ruff check . --fix      # corriger automatiquement ce qui peut l'être
ruff format .           # mettre en forme le code
```

## Règles du jeu

1. Lancez `pytest` avant de commencer : tout doit être vert.
2. Travaillez par petits pas : une amélioration, puis `pytest`, puis un commit.
3. Ne committez jamais avec un test rouge.
4. Un message de commit explicite par amélioration.
5. Notez chaque correction dans votre fichier de synthèse.
