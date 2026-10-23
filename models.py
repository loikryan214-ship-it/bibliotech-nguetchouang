"""Modèles de données de BiblioTech : membres, documents et emprunts.

Chaque classe sait se construire à partir d'une ligne CSV (from_row) ;
Loan sait aussi produire sa ligne (to_row) pour réécrire loans.csv.
"""

from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class Member:
    """Un membre de la bibliothèque."""

    id: str
    name: str
    email: str
    type: str
    active: bool

    @classmethod
    def from_row(cls, row):
        """Construit un Member à partir d'une ligne de members.csv."""
        return cls(
            id=row[0], name=row[1], email=row[2], type=row[3], active=row[4] == "1"
        )


@dataclass
class Loan:
    """Un emprunt ; returned et fee changent au retour du document."""

    id: str
    member_id: str
    book_id: str
    start: str
    due: str
    returned: str = ""
    fee: float = 0

    @classmethod
    def from_row(cls, row):
        """Construit un Loan à partir d'une ligne de loans.csv."""
        try:
            fee = float(row[6])
        except (ValueError, IndexError):
            fee = 0
        return cls(
            id=row[0],
            member_id=row[1],
            book_id=row[2],
            start=row[3],
            due=row[4],
            returned=row[5],
            fee=fee,
        )

    def to_row(self):
        """Ligne de loans.csv correspondant à cet emprunt."""
        fields = [self.id, self.member_id, self.book_id, self.start, self.due]
        return ";".join([*fields, self.returned, f"{self.fee:.2f}"])


@dataclass(frozen=True)
class Book:
    """Un titre du catalogue et son nombre d'exemplaires."""

    id: str
    title: str
    author: str
    kind: str
    price: float
    copies: int

    @classmethod
    def from_row(cls, row):
        """Construit un Book à partir d'une ligne de books.csv."""
        return cls(
            id=row[0],
            title=row[1],
            author=row[2],
            kind=row[3],
            price=float(row[4]),
            copies=int(row[5]),
        )


class LateFee(NamedTuple):
    """Jours de retard d'un emprunt et pénalité correspondante."""

    days: int
    fee: float


@dataclass(frozen=True)
class OverdueLoan:
    """Un emprunt en retard, prêt à être affiché ou rappelé."""

    loan_id: str
    member_name: str
    member_email: str
    title: str
    days_late: int
    fee: float
