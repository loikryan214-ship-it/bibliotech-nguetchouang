# BiblioTech v1.3
# gestion de la bibliotheque municipale
# auteur : stagiaire 2019, modifie par plusieurs personnes depuis

import os
import sys
from datetime import date, datetime, timedelta

DATA = os.environ.get("BIBLIOTECH_DATA", "data")
TODAY = None
debug = False

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


def read_csv_rows(filename):
    """Lignes non vides d'un fichier CSV de DATA (sans l'en-tête), découpées."""
    with open(os.path.join(DATA, filename), encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip().split(";") for line in lines[1:] if line.strip()]


def find_by_id(records, record_id):
    """Premier enregistrement portant cet identifiant, ou None."""
    for record in records:
        if record["id"] == record_id:
            return record
    return None


def is_returned(loan):
    return loan["returned"] != ""


class Library:

    def __init__(self):
        self.books = []
        self.members = []
        self.loans = []
        self.load()

    def load(self):
        """Charge les documents, les membres et les emprunts depuis DATA."""
        for x in read_csv_rows("books.csv"):
            self.books.append({"id": x[0], "title": x[1], "author": x[2], "kind": x[3],
                           "price": float(x[4]), "copies": int(x[5])})
        for x in read_csv_rows("members.csv"):
            self.members.append({"id": x[0], "name": x[1], "email": x[2], "type": x[3],
                           "active": x[4] == "1"})
        for x in read_csv_rows("loans.csv"):
            try:
                fee = float(x[6])
            except (ValueError, IndexError):
                fee = 0
            self.loans.append({"id": x[0], "member": x[1], "book": x[2], "start": x[3],
                           "due": x[4], "returned": x[5], "fee": fee})
        if debug:
            print("chargement ok", len(self.books), len(self.members), len(self.loans))

    def save(self):
        """Réécrit le fichier des emprunts."""
        with open(os.path.join(DATA, "loans.csv"), "w", encoding="utf-8") as f:
            f.write("id;member_id;book_id;start;due;returned;fee\n")
            for x in self.loans:
                fields = [x["id"], x["member"], x["book"], x["start"], x["due"],
                          x["returned"], f"{x['fee']:.2f}"]
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

    def has_open_loan(self, member_id, book_id):
        return any(
            loan["member"] == member_id and loan["book"] == book_id
            for loan in self.open_loans()
        )

    def next_loan_id(self):
        last_number = max((int(loan["id"][1:]) for loan in self.loans), default=0)
        return "L" + str(last_number + 1).zfill(3)

    def borrow_refusal(self, member, book):
        """Motif de refus d'un emprunt, ou None si l'emprunt est autorisé."""
        if not member["active"]:
            return "membre inactif"
        if self.has_overdue_loan(member["id"]):
            return "emprunts en retard"
        limit = MAX_LOANS.get(member["type"], DEFAULT_MAX_LOANS)
        if self.active_loan_count(member["id"]) >= limit:
            return f"limite d'emprunts atteinte ({limit})"
        if self.has_open_loan(member["id"], book["id"]):
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
        refusal = self.borrow_refusal(member, book)
        if refusal is not None:
            print("Refus : " + refusal)
            return False
        start = get_today()
        due = start + timedelta(days=LOAN_DAYS.get(book["kind"], DEFAULT_LOAN_DAYS))
        loan_id = self.next_loan_id()
        self.loans.append({"id": loan_id, "member": member_id, "book": book_id,
                           "start": str(start), "due": str(due), "returned": "",
                           "fee": 0})
        self.save()
        print(f"Emprunt {loan_id} enregistre : {book['title']} pour "
              f"{member['name']}, retour avant le {due}")
        return True

    # retour d'un document
    def return_loan(self, lid):
        ln = self.find_loan(lid)
        if ln is None:
            print("Erreur : emprunt inconnu")
            return
        if ln["returned"] != "":
            print("Erreur : emprunt deja rendu")
            return
        bk = self.find_book(ln["book"])
        mb = self.find_member(ln["member"])
        t = get_today()
        d = max((t - datetime.strptime(ln["due"], DATE_FORMAT).date()).days, 0)
        f = late_fee(d, bk, mb)
        ln["returned"] = str(t)
        ln["fee"] = f
        self.save()
        print("Retour enregistre : " + bk["title"] + ". Retard : " + str(d) + " jour(s). Penalite : " + "%.2f" % f + " EUR")

    # liste des retards + envoi des rappels
    def overdue(self):
        tmp = []
        for x in self.loans:
            if x["returned"] == "":
                if datetime.strptime(x["due"], DATE_FORMAT).date() < get_today():
                    tmp.append(x)
        if len(tmp) == 0:
            print("Aucun retard.")
            return
        tmp.sort(key=lambda x: (x["due"], x["id"]))
        total = 0
        for x in tmp:
            book = self.find_book(x["book"])
            member = self.find_member(x["member"])
            nbj = (get_today() - datetime.strptime(x["due"], DATE_FORMAT).date()).days
            p = late_fee(nbj, book, member)
            total = total + p
            print(x["id"] + " | " + member["name"] + " | " + book["title"] + " | " + str(nbj) + " jour(s) | " + "%.2f" % p + " EUR")
            # envoi du mail
            print("EMAIL -> " + member["email"] + " : Rappel, vous devez rendre '" + book["title"] + "' (retard " + str(nbj) + " jours)")
        print("Total des penalites en cours : " + "%.2f" % total + " EUR")

    def report(self):
        data2 = {}
        print("=== RAPPORT BIBLIOTECH ===")
        print("Date : " + str(get_today()))
        c = 0
        for x in self.books:
            c = c + x["copies"]
        print("Titres : " + str(len(self.books)) + " (" + str(c) + " exemplaires)")
        a = 0
        for x in self.members:
            if x["active"]:
                a = a + 1
        print("Membres : " + str(len(self.members)) + " dont " + str(a) + " actifs")
        en_cours = 0
        en_retard = 0
        encaisse = 0
        a_payer = 0
        for x in self.loans:
            if x["returned"] == "":
                en_cours = en_cours + 1
                due = datetime.strptime(x["due"], DATE_FORMAT).date()
                if due < get_today():
                    en_retard = en_retard + 1
                    bk = self.find_book(x["book"])
                    mb = self.find_member(x["member"])
                    j = (get_today() - due).days
                    a_payer = a_payer + late_fee(j, bk, mb)
            else:
                encaisse = encaisse + x["fee"]
            if x["book"] in data2:
                data2[x["book"]] = data2[x["book"]] + 1
            else:
                data2[x["book"]] = 1
        print("Emprunts : " + str(len(self.loans)) + " au total, " + str(en_cours) + " en cours, " + str(en_retard) + " en retard")
        print("Penalites encaissees : " + "%.2f" % encaisse + " EUR")
        print("Penalites en attente : " + "%.2f" % a_payer + " EUR")
        # par type
        k = {}
        for x in self.loans:
            bk = self.find_book(x["book"])
            if bk["kind"] in k:
                k[bk["kind"]] += 1
            else:
                k[bk["kind"]] = 1
        for kk in sorted(k.keys()):
            print("  - " + kk + " : " + str(k[kk]) + " emprunt(s)")
        # top 3
        lst = []
        for key in data2:
            lst.append((-data2[key], self.find_book(key)["title"]))
        lst.sort()
        print("Top 3 :")
        i = 0
        for x in lst:
            if i < 3:
                print("  " + str(i + 1) + ". " + x[1] + " (" + str(-x[0]) + ")")
            i = i + 1

    def export(self, fname, sep):
        f = open(fname, "w", encoding="utf-8")
        f.write("loan_id" + sep + "member" + sep + "title" + sep + "start" + sep + "due" + sep + "returned" + sep + "days_late" + sep + "fee\n")
        n = 0
        for x in self.loans:
            bk = self.find_book(x["book"])
            mb = self.find_member(x["member"])
            if x["returned"] != "":
                end = datetime.strptime(x["returned"], DATE_FORMAT).date()
            else:
                end = get_today()
            dl = max((end - datetime.strptime(x["due"], DATE_FORMAT).date()).days, 0)
            fee = late_fee(dl, bk, mb)
            f.write(x["id"] + sep + mb["name"] + sep + bk["title"] + sep + x["start"] + sep + x["due"] + sep + x["returned"] + sep + str(dl) + sep + "%.2f" % fee + "\n")
            n = n + 1
        f.close()
        print("Export termine : " + str(n) + " lignes dans " + fname)


def late_fee(days_late, book, member):
    """Pénalité de retard d'un emprunt, arrondie au centime."""
    if days_late <= 0:
        return 0
    fee = days_late * DAILY_FEE.get(book["kind"], DEFAULT_DAILY_FEE)
    fee = fee * FEE_RATE.get(member["type"], DEFAULT_FEE_RATE)
    return round(min(fee, book["price"]), 2)


def parse_date(text):
    return datetime.strptime(text, DATE_FORMAT).date()


def days_late(loan, end):
    """Jours de retard d'un emprunt à la date end (0 s'il n'est pas en retard)."""
    return max((end - parse_date(loan["due"])).days, 0)


def is_overdue(loan):
    return not is_returned(loan) and parse_date(loan["due"]) < get_today()


def get_today():
    global TODAY
    if TODAY is None:
        return date.today()
    return TODAY


def process(args):
    global TODAY
    lib = Library()
    if len(args) == 0:
        print("Usage : python bibliotech.py <commande> [arguments] [--today AAAA-MM-JJ]")
        print("Commandes : list, members, borrow, return, overdue, report, export")
        return 1
    cmd = args[0]
    if cmd == "list":
        for x in lib.books:
            n = lib.available_copies(x["id"])
            print(x["id"] + " | " + x["title"] + " | " + x["author"] + " | " + x["kind"] + " | " + str(n) + "/" + str(x["copies"]) + " disponible(s)")
    elif cmd == "members":
        for x in lib.members:
            if x["active"]:
                s = "actif"
            else:
                s = "inactif"
            print(x["id"] + " | " + x["name"] + " | " + x["type"] + " | " + s + " | " + str(lib.active_loan_count(x["id"])) + " emprunt(s) en cours")
    elif cmd == "borrow":
        if len(args) < 3:
            print("Usage : borrow <id_membre> <id_document>")
            return 1
        r = lib.borrow(args[1], args[2])
        if not r:
            return 2
    elif cmd == "return":
        if len(args) < 2:
            print("Usage : return <id_emprunt>")
            return 1
        lib.return_loan(args[1])
    elif cmd == "overdue":
        lib.overdue()
    elif cmd == "report":
        lib.report()
    elif cmd == "export":
        if len(args) < 2:
            print("Usage : export <fichier.csv>")
            return 1
        lib.export(args[1], ";")
    else:
        print("Commande inconnue : " + cmd)
        return 1
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--today" in a:
        i = a.index("--today")
        TODAY = datetime.strptime(a[i + 1], DATE_FORMAT).date()
        a = a[:i] + a[i + 2:]
    if "--debug" in a:
        debug = True
        a.remove("--debug")
    sys.exit(process(a))
