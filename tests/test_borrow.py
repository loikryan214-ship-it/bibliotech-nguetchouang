"""Tests unitaires des emprunts (Library.borrow), au 21/10/2026."""

import pytest


@pytest.mark.parametrize(
    ("member_id", "book_id", "reason"),
    [
        pytest.param("M004", "B002", "membre inactif", id="membre_inactif"),
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
    assert library.borrow("M005", "B005") is True
    assert library.borrow("M005", "B002") is True
    capsys.readouterr()

    accepted = library.borrow("M005", "B007")

    assert accepted is False
    assert "limite d'emprunts atteinte (3)" in capsys.readouterr().out


def test_accepted_borrow_creates_next_loan_due_in_seven_days_for_a_dvd(library, capsys):
    accepted = library.borrow("M005", "B005")

    assert accepted is True
    loan = library.find_loan("L013")
    assert loan.member_id == "M005"
    assert loan.book_id == "B005"
    assert loan.due == "2026-10-28"
    assert "Emprunt L013 enregistre" in capsys.readouterr().out


def test_create_loan_records_and_returns_the_loan_without_printing(library, capsys):
    member = library.find_member("M005")
    book = library.find_book("B005")

    loan = library.create_loan(member, book)

    assert loan.id == "L013"
    assert loan.due == "2026-10-28"
    assert library.find_loan("L013") is loan
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("member_id", "allowed_books", "extra_book", "limit"),
    [
        pytest.param(
            "M007",
            ["B001", "B002", "B005", "B006", "B007"],
            "B009",
            5,
            id="etudiant_limite_a_5",
        ),
        pytest.param(
            "M008",
            ["B001", "B002", "B005", "B006", "B007", "B009", "B010", "B011"],
            "B012",
            8,
            id="premium_limite_a_8",
        ),
    ],
)
def test_member_is_refused_beyond_their_loan_limit(
    library, capsys, member_id, allowed_books, extra_book, limit
):
    for book_id in allowed_books:
        assert library.borrow(member_id, book_id) is True
    capsys.readouterr()

    accepted = library.borrow(member_id, extra_book)

    assert accepted is False
    assert f"limite d'emprunts atteinte ({limit})" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("book_id", "due"),
    [
        pytest.param("B002", "2026-11-11", id="livre_21_jours"),
        pytest.param("B005", "2026-10-28", id="dvd_7_jours"),
        pytest.param("B007", "2026-10-24", id="magazine_3_jours"),
    ],
)
def test_loan_duration_depends_on_document_kind(library, book_id, due):
    library.borrow("M005", book_id)

    assert library.find_loan("L013").due == due


@pytest.mark.parametrize(
    ("member_id", "book_id", "error"),
    [
        pytest.param("M999", "B001", "Erreur : membre inconnu", id="membre_inconnu"),
        pytest.param("M005", "B999", "Erreur : livre inconnu", id="livre_inconnu"),
    ],
)
def test_borrow_with_unknown_id_is_rejected(library, capsys, member_id, book_id, error):
    loans_before = len(library.loans)

    accepted = library.borrow(member_id, book_id)

    assert accepted is False
    assert error in capsys.readouterr().out
    assert len(library.loans) == loans_before
