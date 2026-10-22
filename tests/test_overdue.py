"""Tests unitaires du calcul des retards (find_overdue_loans), au 21/10/2026."""

from datetime import date

import pytest


def test_find_overdue_loans_lists_late_loans_sorted_by_due_date(library):
    overdue = library.find_overdue_loans()

    assert [item.loan_id for item in overdue] == ["L003", "L004", "L005", "L007"]


def test_find_overdue_loans_computes_days_and_fees(library):
    overdue = library.find_overdue_loans()

    assert [item.days_late for item in overdue] == [15, 13, 10, 3]
    assert [item.fee for item in overdue] == pytest.approx([7.50, 6.50, 0.00, 0.30])


def test_find_overdue_loans_does_not_print_anything(library, capsys):
    library.find_overdue_loans()

    assert capsys.readouterr().out == ""


def test_overdue_loan_carries_reminder_details(library):
    first = library.find_overdue_loans()[0]

    assert first.member_name == "Bruno Lefevre"
    assert first.member_email == "bruno.lefevre@example.com"
    assert first.title == "Fondation"


def test_loan_fee_names_days_late_and_fee(library):
    loan = library.find_loan("L003")

    result = library.loan_fee(loan, date(2026, 10, 21))

    assert result.days == 15
    assert result.fee == pytest.approx(7.50)
