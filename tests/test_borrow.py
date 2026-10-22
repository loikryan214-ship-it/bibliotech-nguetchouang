"""Tests unitaires des emprunts (Library.borrow), au 21/10/2026."""

import pytest


def test_inactive_member_is_refused(library, capsys):
    accepted = library.borrow("M004", "B002")

    assert accepted is False
    assert "membre inactif" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("member_id", "book_id", "reason"),
    [
        pytest.param("M001", "B002", "emprunts en retard", id="membre_en_retard"),
        pytest.param(
            "M005", "B001", "deja emprunte par ce membre", id="document_deja_emprunte"
        ),
        pytest.param(
            "M005", "B003", "plus d'exemplaire disponible", id="aucun_exemplaire_libre"
        ),
    ],
)
def test_borrow_is_refused_with_reason(library, capsys, member_id, book_id, reason):
    loans_before = len(library.loans)

    accepted = library.borrow(member_id, book_id)

    assert accepted is False
    assert f"Refus : {reason}" in capsys.readouterr().out
    assert len(library.loans) == loans_before


def test_standard_member_is_refused_beyond_three_loans(library, capsys):
    library.borrow("M005", "B005")
    library.borrow("M005", "B002")
    capsys.readouterr()

    accepted = library.borrow("M005", "B007")

    assert accepted is False
    assert "limite d'emprunts atteinte (3)" in capsys.readouterr().out


def test_accepted_borrow_creates_next_loan_due_in_seven_days_for_a_dvd(library, capsys):
    accepted = library.borrow("M005", "B005")

    assert accepted is True
    loan = library.find_loan("L013")
    assert loan["member"] == "M005"
    assert loan["book"] == "B005"
    assert loan["due"] == "2026-10-28"
    assert "Emprunt L013 enregistre" in capsys.readouterr().out


def test_create_loan_records_and_returns_the_loan_without_printing(library, capsys):
    member = library.find_member("M005")
    book = library.find_book("B005")

    loan = library.create_loan(member, book)

    assert loan["id"] == "L013"
    assert loan["due"] == "2026-10-28"
    assert library.find_loan("L013") is loan
    assert capsys.readouterr().out == ""
