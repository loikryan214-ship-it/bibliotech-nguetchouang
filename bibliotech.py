# BiblioTech v1.3
# gestion de la bibliotheque municipale
# auteur : stagiaire 2019, modifie par plusieurs personnes depuis

import os, sys
import datetime
from datetime import *
import json

DATA = os.environ.get("BIBLIOTECH_DATA", "data")
TODAY = None
debug = False
cache = {}


class Library:

    def __init__(self):
        self.b = []
        self.m = []
        self.l = []
        self.plugins = {}
        self.load()

    # chargement des donnees
    def load(self):
        f = open(DATA + "/books.csv")
        lines = f.readlines()
        f.close()
        for line in lines[1:]:
            if line.strip() == "":
                continue
            x = line.strip().split(";")
            self.b.append({"id": x[0], "title": x[1], "author": x[2], "kind": x[3], "price": eval(x[4]), "copies": int(x[5])})
        f = open(DATA + "/members.csv")
        lines = f.readlines()
        f.close()
        for line in lines[1:]:
            if line.strip() == "":
                continue
            x = line.strip().split(";")
            if x[4] == "1":
                a = True
            else:
                a = False
            self.m.append({"id": x[0], "name": x[1], "email": x[2], "type": x[3], "active": a})
        f = open(DATA + "/loans.csv")
        lines = f.readlines()
        f.close()
        for line in lines[1:]:
            if line.strip() == "":
                continue
            x = line.strip().split(";")
            try:
                fee = float(x[6])
            except:
                fee = 0
            self.l.append({"id": x[0], "member": x[1], "book": x[2], "start": x[3], "due": x[4], "returned": x[5], "fee": fee})
        if debug == True:
            print("chargement ok", len(self.b), len(self.m), len(self.l))

    def save(self):
        f = open(DATA + "/loans.csv", "w")
        f.write("id;member_id;book_id;start;due;returned;fee\n")
        for x in self.l:
            f.write(x["id"] + ";" + x["member"] + ";" + x["book"] + ";" + x["start"] + ";" + x["due"] + ";" + x["returned"] + ";" + "%.2f" % x["fee"] + "\n")
        f.close()

    # t = "b" pour livre, "m" pour membre, "l" pour emprunt
    def find(self, t, id):
        if t == "b":
            for x in self.b:
                if x["id"] == id:
                    return x
        elif t == "m":
            for x in self.m:
                if x["id"] == id:
                    return x
        elif t == "l":
            for x in self.l:
                if x["id"] == id:
                    return x
        return None

    def nb(self, mid):
        n = 0
        for x in self.l:
            if x["member"] == mid and x["returned"] == "":
                n = n + 1
        return n

    def dispo(self, bid):
        bk = self.find("b", bid)
        n = 0
        for x in self.l:
            if x["book"] == bid and x["returned"] == "":
                n = n + 1
        return bk["copies"] - n

    # emprunter un document
    def do_stuff(self, mid, bid):
        mb = self.find("m", mid)
        if mb != None:
            bk = self.find("b", bid)
            if bk != None:
                if mb["active"] == True:
                    # verif retards
                    late = False
                    for x in self.l:
                        if x["member"] == mid and x["returned"] == "":
                            if datetime.strptime(x["due"], "%Y-%m-%d").date() < get_today():
                                late = True
                    if late == False:
                        # verif nombre max
                        if mb["type"] == "student":
                            mx = 5
                        elif mb["type"] == "premium":
                            mx = 8
                        else:
                            mx = 3
                        if self.nb(mid) < mx:
                            deja = False
                            for x in self.l:
                                if x["member"] == mid and x["book"] == bid and x["returned"] == "":
                                    deja = True
                            if not deja:
                                if self.dispo(bid) > 0:
                                    # duree selon le type
                                    if bk["kind"] == "book":
                                        d = 21
                                    elif bk["kind"] == "dvd":
                                        d = 7
                                    elif bk["kind"] == "magazine":
                                        d = 3
                                    else:
                                        d = 21
                                    t = get_today()
                                    due = t + timedelta(days=d)
                                    mx2 = 0
                                    for x in self.l:
                                        if int(x["id"][1:]) > mx2:
                                            mx2 = int(x["id"][1:])
                                    new_id = "L" + str(mx2 + 1).zfill(3)
                                    self.l.append({"id": new_id, "member": mid, "book": bid, "start": str(t), "due": str(due), "returned": "", "fee": 0})
                                    self.save()
                                    print("Emprunt " + new_id + " enregistre : " + bk["title"] + " pour " + mb["name"] + ", retour avant le " + str(due))
                                    return True
                                else:
                                    print("Refus : plus d'exemplaire disponible")
                                    return False
                            else:
                                print("Refus : deja emprunte par ce membre")
                                return False
                        else:
                            print("Refus : limite d'emprunts atteinte (" + str(mx) + ")")
                            return False
                    else:
                        print("Refus : emprunts en retard")
                        return False
                else:
                    print("Refus : membre inactif")
                    return False
            else:
                print("Erreur : livre inconnu")
                return False
        else:
            print("Erreur : membre inconnu")
            return False

    # retour d'un document
    def ret(self, lid):
        ln = self.find("l", lid)
        if ln == None:
            print("Erreur : emprunt inconnu")
            return
        if ln["returned"] != "":
            print("Erreur : emprunt deja rendu")
            return
        bk = self.find("b", ln["book"])
        mb = self.find("m", ln["member"])
        t = get_today()
        d = (t - datetime.strptime(ln["due"], "%Y-%m-%d").date()).days
        if d > 0:
            if bk["kind"] == "book":
                f = d * 0.5
            elif bk["kind"] == "dvd":
                f = d * 1.0
            elif bk["kind"] == "magazine":
                f = d * 0.2
            else:
                f = d * 0.5
            if mb["type"] == "student":
                f = f * 0.5
            elif mb["type"] == "premium":
                f = 0
            if f > bk["price"]:
                f = bk["price"]
        else:
            f = 0
            d = 0
        f = round(f, 2)
        ln["returned"] = str(t)
        ln["fee"] = f
        self.save()
        print("Retour enregistre : " + bk["title"] + ". Retard : " + str(d) + " jour(s). Penalite : " + "%.2f" % f + " EUR")

    # liste des retards + envoi des rappels
    def overdue(self):
        tmp = []
        for x in self.l:
            if x["returned"] == "":
                if datetime.strptime(x["due"], "%Y-%m-%d").date() < get_today():
                    tmp.append(x)
        if len(tmp) == 0:
            print("Aucun retard.")
            return
        tmp.sort(key=lambda x: (x["due"], x["id"]))
        total = 0
        for x in tmp:
            book = self.find("b", x["book"])
            member = self.find("m", x["member"])
            nbj = (get_today() - datetime.strptime(x["due"], "%Y-%m-%d").date()).days
            # calcul penalite
            if nbj > 0:
                if book["kind"] == "book":
                    p = nbj * 0.5
                elif book["kind"] == "dvd":
                    p = nbj * 1.0
                elif book["kind"] == "magazine":
                    p = nbj * 0.2
                else:
                    p = nbj * 0.5
                if member["type"] == "student":
                    p = p * 0.5
                elif member["type"] == "premium":
                    p = 0
                if p > book["price"]:
                    p = book["price"]
            else:
                p = 0
            p = round(p, 2)
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
        for x in self.b:
            c = c + x["copies"]
        print("Titres : " + str(len(self.b)) + " (" + str(c) + " exemplaires)")
        a = 0
        for x in self.m:
            if x["active"] == True:
                a = a + 1
        print("Membres : " + str(len(self.m)) + " dont " + str(a) + " actifs")
        en_cours = 0
        en_retard = 0
        encaisse = 0
        a_payer = 0
        for x in self.l:
            if x["returned"] == "":
                en_cours = en_cours + 1
                due = datetime.strptime(x["due"], "%Y-%m-%d").date()
                if due < get_today():
                    en_retard = en_retard + 1
                    bk = self.find("b", x["book"])
                    mb = self.find("m", x["member"])
                    j = (get_today() - due).days
                    if j > 0:
                        if bk["kind"] == "book":
                            pen = j * 0.5
                        elif bk["kind"] == "dvd":
                            pen = j * 1.0
                        elif bk["kind"] == "magazine":
                            pen = j * 0.2
                        else:
                            pen = j * 0.5
                        if mb["type"] == "student":
                            pen = pen * 0.5
                        elif mb["type"] == "premium":
                            pen = 0
                        if pen > bk["price"]:
                            pen = bk["price"]
                    else:
                        pen = 0
                    a_payer = a_payer + round(pen, 2)
            else:
                encaisse = encaisse + x["fee"]
            if x["book"] in data2:
                data2[x["book"]] = data2[x["book"]] + 1
            else:
                data2[x["book"]] = 1
        print("Emprunts : " + str(len(self.l)) + " au total, " + str(en_cours) + " en cours, " + str(en_retard) + " en retard")
        print("Penalites encaissees : " + "%.2f" % encaisse + " EUR")
        print("Penalites en attente : " + "%.2f" % a_payer + " EUR")
        # par type
        k = {}
        for x in self.l:
            bk = self.find("b", x["book"])
            if bk["kind"] in k:
                k[bk["kind"]] += 1
            else:
                k[bk["kind"]] = 1
        for kk in sorted(k.keys()):
            print("  - " + kk + " : " + str(k[kk]) + " emprunt(s)")
        # top 3
        lst = []
        for key in data2:
            lst.append((-data2[key], self.find("b", key)["title"]))
        lst.sort()
        print("Top 3 :")
        i = 0
        for x in lst:
            if i < 3:
                print("  " + str(i + 1) + ". " + x[1] + " (" + str(-x[0]) + ")")
            i = i + 1

    def export(self, fname, sep):
        f = open(fname, "w")
        f.write("loan_id" + sep + "member" + sep + "title" + sep + "start" + sep + "due" + sep + "returned" + sep + "days_late" + sep + "fee\n")
        n = 0
        for x in self.l:
            bk = self.find("b", x["book"])
            mb = self.find("m", x["member"])
            if x["returned"] != "":
                end = datetime.strptime(x["returned"], "%Y-%m-%d").date()
            else:
                end = get_today()
            dl = (end - datetime.strptime(x["due"], "%Y-%m-%d").date()).days
            if dl > 0:
                if bk["kind"] == "book":
                    fee = dl * 0.5
                elif bk["kind"] == "dvd":
                    fee = dl * 1.0
                elif bk["kind"] == "magazine":
                    fee = dl * 0.2
                else:
                    fee = dl * 0.5
                if mb["type"] == "student":
                    fee = fee * 0.5
                elif mb["type"] == "premium":
                    fee = 0
                if fee > bk["price"]:
                    fee = bk["price"]
            else:
                fee = 0
                dl = 0
            fee = round(fee, 2)
            f.write(x["id"] + sep + mb["name"] + sep + bk["title"] + sep + x["start"] + sep + x["due"] + sep + x["returned"] + sep + str(dl) + sep + "%.2f" % fee + "\n")
            n = n + 1
        f.close()
        print("Export termine : " + str(n) + " lignes dans " + fname)

    # systeme de plugins (pour plus tard)
    def register_plugin(self, name, fn, priority=0, options={}):
        self.plugins[name] = {"fn": fn, "priority": priority, "options": options}

    def run_plugins(self, event, payload=None):
        res = []
        for name in sorted(self.plugins, key=lambda n: self.plugins[n]["priority"]):
            try:
                res.append(self.plugins[name]["fn"](event, payload, **self.plugins[name]["options"]))
            except:
                pass
        return res


def get_today():
    global TODAY
    if TODAY == None:
        return date.today()
    return TODAY


# ancienne version du calcul, ne plus utiliser
def old_calc_fee(days, kind):
    if kind == "book":
        return days * 0.3
    return days * 0.8


def process(args):
    global TODAY
    lib = Library()
    if len(args) == 0:
        print("Usage : python bibliotech.py <commande> [arguments] [--today AAAA-MM-JJ]")
        print("Commandes : list, members, borrow, return, overdue, report, export")
        return 1
    cmd = args[0]
    if cmd == "list":
        for x in lib.b:
            n = lib.dispo(x["id"])
            print(x["id"] + " | " + x["title"] + " | " + x["author"] + " | " + x["kind"] + " | " + str(n) + "/" + str(x["copies"]) + " disponible(s)")
    elif cmd == "members":
        for x in lib.m:
            if x["active"]:
                s = "actif"
            else:
                s = "inactif"
            print(x["id"] + " | " + x["name"] + " | " + x["type"] + " | " + s + " | " + str(lib.nb(x["id"])) + " emprunt(s) en cours")
    elif cmd == "borrow":
        if len(args) < 3:
            print("Usage : borrow <id_membre> <id_document>")
            return 1
        r = lib.do_stuff(args[1], args[2])
        if r == False:
            return 2
    elif cmd == "return":
        if len(args) < 2:
            print("Usage : return <id_emprunt>")
            return 1
        lib.ret(args[1])
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
        TODAY = datetime.strptime(a[i + 1], "%Y-%m-%d").date()
        a = a[:i] + a[i + 2:]
    if "--debug" in a:
        debug = True
        a.remove("--debug")
    sys.exit(process(a))
