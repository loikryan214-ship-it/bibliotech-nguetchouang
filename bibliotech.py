"""BiblioTech : gestion en ligne de commande d'une bibliothèque municipale.

Catalogue, membres, emprunts, retours, pénalités de retard, rappels et rapports.
Voir README.md pour les commandes disponibles et les règles métier.
"""

import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta

# Dossier des fichiers CSV (modifiable par la variable d'environnement)
DATA = os.environ.get("BIBLIOTECH_DATA", "data")
# Réglés par les options --today et --debug de la ligne de commande
TODAY = None
DEBUG = False

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_REFUSED = 2

DATE_FORMAT = "%Y-%m-%d"

# Durée d'emprunt en jours, selon le type de document
LOAN_DAYS = {"book": 21, "dvd": 7, "magazine": 3}
DEFAULT_LOAN_DAYS = LOAN_DAYS["book"]

# Nombre maximum d'emprunts simultanés, selon le type de membre
MAX_LOANS = {"student": 5, "premium": 8}
DEFAULT_MAX_LOANS = 3

# Pénalité par jour de retard (EUR), selon le type de document
DAILY_FEE = {"book": 0.5, "dvd": 1.0, "magazine": 0.2}
DEFAULT_DAILY_FEE = DAILY_FEE["book"]

# Coefficient appliqué à la pénalité, selon le type de membre
FEE_RATE = {"student": 0.5, "premium": 0}
DEFAULT_FEE_RATE = 1

# Nombre de documents affichés dans le classement du rapport
TOP_BOOKS_COUNT = 3


def read_csv_rows(filename):
    """Lignes non vides d'un fichier CSV de DATA (sans l'en-tête), découpées."""
    with open(os.path.join(DATA, filename), encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip().split(";") for line in lines[1:] if line.strip()]


def parse_book(row):
    return {
        "id": row[0],
        "title": row[1],
        "author": row[2],
        "kind": row[3],
        "price": float(row[4]),
        "copies": int(row[5]),
    }


def parse_member(row):
    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "type": row[3],
        "active": row[4] == "1",
    }


def parse_loan(row):
    try:
        fee = float(row[6])
    except (ValueError, IndexError):
        fee = 0
    return {
        "id": row[0],
        "member": row[1],
        "book": row[2],
        "start": row[3],
        "due": row[4],
        "returned": row[5],
        "fee": fee,
    }


def find_by_id(records, record_id):
    """Premier enregistrement portant cet identifiant, ou None."""
    for record in records:
        if record["id"] == record_id:
            return record
    return None


def is_returned(loan):
    return loan["returned"] != ""


@dataclass(frozen=True)
class OverdueLoan:
    """Un emprunt en retard, prêt à être affiché ou rappelé."""

    loan_id: str
    member_name: str
    member_email: str
    title: str
    days_late: int
    fee: float


class Library:
    def __init__(self):
        self.books = []
        self.members = []
        self.loans = []
        self.load()

    def load(self):
        """Charge les documents, les membres et les emprunts depuis DATA."""
        self.books = [parse_book(row) for row in read_csv_rows("books.csv")]
        self.members = [parse_member(row) for row in read_csv_rows("members.csv")]
        self.loans = [parse_loan(row) for row in read_csv_rows("loans.csv")]
        if DEBUG:
            print("chargement ok", len(self.books), len(self.members), len(self.loans))

    def save(self):
        """Réécrit le fichier des emprunts."""
        with open(os.path.join(DATA, "loans.csv"), "w", encoding="utf-8") as f:
            f.write("id;member_id;book_id;start;due;returned;fee\n")
            for loan in self.loans:
                fields = [
                    loan["id"],
                    loan["member"],
                    loan["book"],
                    loan["start"],
                    loan["due"],
                    loan["returned"],
                    f"{loan['fee']:.2f}",
                ]
                f.write(";".join(fields) + "\n")

    def find_book(self, book_id):
        return find_by_id(self.books, book_id)

    def find_member(self, member_id):
        return find_by_id(self.members, member_id)

    def find_loan(self, loan_id):
        return find_by_id(self.loans, loan_id)

    def open_loans(self):
        """Emprunts pas encore rendus."""
        return [loan for loan in self.loans if not is_returned(loan)]

    def active_loan_count(self, member_id):
        return sum(1 for loan in self.open_loans() if loan["member"] == member_id)

    def available_copies(self, book_id):
        book = self.find_book(book_id)
        borrowed = sum(1 for loan in self.open_loans() if loan["book"] == book_id)
        return book["copies"] - borrowed

    def has_overdue_loan(self, member_id):
        return any(
            loan["member"] == member_id and is_overdue(loan)
            for loan in self.open_loans()
        )

    def is_borrowing(self, member_id, book_id):
        return any(
            loan["member"] == member_id and loan["book"] == book_id
            for loan in self.open_loans()
        )

    def next_loan_id(self):
        last_number = max((int(loan["id"][1:]) for loan in self.loans), default=0)
        return "L" + str(last_number + 1).zfill(3)

    def refusal_reason(self, member, book):
        """Motif de refus d'un emprunt, ou None si l'emprunt est autorisé."""
        if not member["active"]:
            return "membre inactif"
        if self.has_overdue_loan(member["id"]):
            return "emprunts en retard"
        limit = MAX_LOANS.get(member["type"], DEFAULT_MAX_LOANS)
        if self.active_loan_count(member["id"]) >= limit:
            return f"limite d'emprunts atteinte ({limit})"
        if self.is_borrowing(member["id"], book["id"]):
            return "deja emprunte par ce membre"
        if self.available_copies(book["id"]) <= 0:
            return "plus d'exemplaire disponible"
        return None

    def borrow(self, member_id, book_id):
        """Enregistre un emprunt. Renvoie True s'il a été accepté."""
        member = self.find_member(member_id)
        if member is None:
            print("Erreur : membre inconnu")
            return False
        book = self.find_book(book_id)
        if book is None:
            print("Erreur : livre inconnu")
            return False
        refusal = self.refusal_reason(member, book)
        if refusal is not None:
            print("Refus : " + refusal)
            return False
        self.create_loan(member, book)
        return True

    def create_loan(self, member, book):
        """Calcule l'échéance et l'identifiant, enregistre et confirme l'emprunt."""
        start = get_today()
        due = start + timedelta(days=LOAN_DAYS.get(book["kind"], DEFAULT_LOAN_DAYS))
        loan_id = self.next_loan_id()
        self.loans.append(
            {
                "id": loan_id,
                "member": member["id"],
                "book": book["id"],
                "start": str(start),
                "due": str(due),
                "returned": "",
                "fee": 0,
            }
        )
        self.save()
        print(
            f"Emprunt {loan_id} enregistre : {book['title']} pour "
            f"{member['name']}, retour avant le {due}"
        )

    def loan_fee(self, loan, end):
        """Jours de retard et pénalité d'un emprunt à la date end."""
        days = days_late(loan, end)
        book = self.find_book(loan["book"])
        member = self.find_member(loan["member"])
        return days, late_fee(days, book["kind"], member["type"], book["price"])

    def return_loan(self, loan_id):
        """Enregistre le retour d'un emprunt et sa pénalité éventuelle."""
        loan = self.find_loan(loan_id)
        if loan is None:
            print("Erreur : emprunt inconnu")
            return
        if is_returned(loan):
            print("Erreur : emprunt deja rendu")
            return
        today = get_today()
        days, fee = self.loan_fee(loan, today)
        loan["returned"] = str(today)
        loan["fee"] = fee
        self.save()
        title = self.find_book(loan["book"])["title"]
        print(
            f"Retour enregistre : {title}. Retard : {days} jour(s). "
            f"Penalite : {fee:.2f} EUR"
        )

    def overdue_loans(self):
        return [loan for loan in self.loans if is_overdue(loan)]

    def find_overdue_loans(self):
        """Emprunts en retard, triés par échéance, sans rien afficher."""
        late_loans = sorted(self.overdue_loans(), key=lambda x: (x["due"], x["id"]))
        result = []
        for loan in late_loans:
            book = self.find_book(loan["book"])
            member = self.find_member(loan["member"])
            days, fee = self.loan_fee(loan, get_today())
            result.append(
                OverdueLoan(
                    loan_id=loan["id"],
                    member_name=member["name"],
                    member_email=member["email"],
                    title=book["title"],
                    days_late=days,
                    fee=fee,
                )
            )
        return result

    def overdue(self):
        """Affiche les retards et envoie un rappel à chaque emprunteur."""
        print_overdue_loans(self.find_overdue_loans())

    def report(self):
        """Affiche le rapport d'activité de la bibliothèque."""
        print("=== RAPPORT BIBLIOTECH ===")
        print(f"Date : {get_today()}")
        self.print_collection_summary()
        self.print_loan_summary()
        self.print_loans_by_kind()
        self.print_top_books(TOP_BOOKS_COUNT)

    def print_collection_summary(self):
        copies = sum(book["copies"] for book in self.books)
        active = sum(1 for member in self.members if member["active"])
        print(f"Titres : {len(self.books)} ({copies} exemplaires)")
        print(f"Membres : {len(self.members)} dont {active} actifs")

    def print_loan_summary(self):
        late_loans = self.overdue_loans()
        collected = sum(loan["fee"] for loan in self.loans if is_returned(loan))
        pending = sum(self.loan_fee(loan, get_today())[1] for loan in late_loans)
        print(
            f"Emprunts : {len(self.loans)} au total, {len(self.open_loans())} "
            f"en cours, {len(late_loans)} en retard"
        )
        print(f"Penalites encaissees : {collected:.2f} EUR")
        print(f"Penalites en attente : {pending:.2f} EUR")

    def print_loans_by_kind(self):
        counts = Counter(self.find_book(loan["book"])["kind"] for loan in self.loans)
        for kind in sorted(counts):
            print(f"  - {kind} : {counts[kind]} emprunt(s)")

    def print_top_books(self, limit):
        counts = Counter(loan["book"] for loan in self.loans)
        ranking = sorted(
            (-count, self.find_book(book_id)["title"])
            for book_id, count in counts.items()
        )
        print(f"Top {limit} :")
        for rank, (negative_count, title) in enumerate(ranking[:limit], start=1):
            print(f"  {rank}. {title} ({-negative_count})")

    def export(self, filename, sep=";"):
        """Exporte tous les emprunts, avec leur retard et leur pénalité."""
        header = [
            "loan_id",
            "member",
            "title",
            "start",
            "due",
            "returned",
            "days_late",
            "fee",
        ]
        with open(filename, "w", encoding="utf-8") as f:
            f.write(sep.join(header) + "\n")
            for loan in self.loans:
                end = parse_date(loan["returned"]) if is_returned(loan) else get_today()
                days, fee = self.loan_fee(loan, end)
                fields = [
                    loan["id"],
                    self.find_member(loan["member"])["name"],
                    self.find_book(loan["book"])["title"],
                    loan["start"],
                    loan["due"],
                    loan["returned"],
                    str(days),
                    f"{fee:.2f}",
                ]
                f.write(sep.join(fields) + "\n")
        print(f"Export termine : {len(self.loans)} lignes dans {filename}")


def late_fee(days_late: int, kind: str, member_type: str, price: float) -> float:
    """Pénalité de retard, réduite selon le membre et plafonnée au prix."""
    if days_late <= 0:
        return 0.0
    fee = days_late * DAILY_FEE.get(kind, DEFAULT_DAILY_FEE)
    fee = fee * FEE_RATE.get(member_type, DEFAULT_FEE_RATE)
    return round(min(fee, price), 2)


def parse_date(text: str) -> date:
    return datetime.strptime(text, DATE_FORMAT).date()


def days_late(loan, end):
    """Jours de retard d'un emprunt à la date end (0 s'il n'est pas en retard)."""
    return max((end - parse_date(loan["due"])).days, 0)


def is_overdue(loan):
    return not is_returned(loan) and parse_date(loan["due"]) < get_today()


def print_overdue_loans(overdue_loans):
    """Affiche les retards, envoie les rappels et le total des pénalités."""
    if not overdue_loans:
        print("Aucun retard.")
        return
    for item in overdue_loans:
        print(
            f"{item.loan_id} | {item.member_name} | {item.title} | "
            f"{item.days_late} jour(s) | {item.fee:.2f} EUR"
        )
        send_reminder(item)
    total = sum(item.fee for item in overdue_loans)
    print(f"Total des penalites en cours : {total:.2f} EUR")


def send_reminder(item):
    """Envoi (simulé) d'un e-mail de rappel."""
    print(
        f"EMAIL -> {item.member_email} : Rappel, vous devez rendre "
        f"'{item.title}' (retard {item.days_late} jours)"
    )


def get_today():
    """Date du jour, ou date simulée avec l'option --today."""
    return date.today() if TODAY is None else TODAY


def cmd_list(lib, params):
    for book in lib.books:
        available = lib.available_copies(book["id"])
        print(
            f"{book['id']} | {book['title']} | {book['author']} | {book['kind']} | "
            f"{available}/{book['copies']} disponible(s)"
        )
    return EXIT_OK


def cmd_members(lib, params):
    for member in lib.members:
        status = "actif" if member["active"] else "inactif"
        count = lib.active_loan_count(member["id"])
        print(
            f"{member['id']} | {member['name']} | {member['type']} | {status} | "
            f"{count} emprunt(s) en cours"
        )
    return EXIT_OK


def cmd_borrow(lib, params):
    accepted = lib.borrow(params[0], params[1])
    return EXIT_OK if accepted else EXIT_REFUSED


def cmd_return(lib, params):
    lib.return_loan(params[0])
    return EXIT_OK


def cmd_overdue(lib, params):
    lib.overdue()
    return EXIT_OK


def cmd_report(lib, params):
    lib.report()
    return EXIT_OK


def cmd_export(lib, params):
    lib.export(params[0])
    return EXIT_OK


# nom de la commande -> (nombre d'arguments requis, message d'usage, fonction)
COMMANDS = {
    "list": (0, None, cmd_list),
    "members": (0, None, cmd_members),
    "borrow": (2, "Usage : borrow <id_membre> <id_document>", cmd_borrow),
    "return": (1, "Usage : return <id_emprunt>", cmd_return),
    "overdue": (0, None, cmd_overdue),
    "report": (0, None, cmd_report),
    "export": (1, "Usage : export <fichier.csv>", cmd_export),
}


def process(args):
    """Exécute une commande et renvoie le code de sortie."""
    if not args:
        print(
            "Usage : python bibliotech.py <commande> [arguments] [--today AAAA-MM-JJ]"
        )
        print("Commandes : " + ", ".join(COMMANDS))
        return EXIT_USAGE
    name, params = args[0], args[1:]
    if name not in COMMANDS:
        print("Commande inconnue : " + name)
        return EXIT_USAGE
    required, usage, handler = COMMANDS[name]
    if len(params) < required:
        print(usage)
        return EXIT_USAGE
    return handler(Library(), params)


def parse_options(argv):
    """Retire --today et --debug des arguments ; renvoie (args, today, debug)."""
    args = list(argv)
    today = None
    if "--today" in args:
        i = args.index("--today")
        today = parse_date(args[i + 1])
        del args[i : i + 2]
    debug = "--debug" in args
    if debug:
        args.remove("--debug")
    return args, today, debug


def main(argv):
    global TODAY, DEBUG
    args, TODAY, DEBUG = parse_options(argv)
    return process(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
