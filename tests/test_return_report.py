"""Tests unitaires du retour, du rapport et de l'export, au 21/10/2026."""

from pathlib import Path

import pytest


def test_late_return_records_capped_student_fee(library, capsys):
    library.return_loan("L004")  # DVD rendu 13 jours en retard par une étudiante

    loan = library.find_loan("L004")
    assert loan.returned == "2026-10-21"
    assert loan.fee == pytest.approx(6.50)
    assert "Retard : 13 jour(s). Penalite : 6.50 EUR" in capsys.readouterr().out


def test_on_time_return_records_no_fee(library, capsys):
    library.return_loan("L006")

    assert library.find_loan("L006").fee == 0
    assert "Retard : 0 jour(s). Penalite : 0.00 EUR" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("loan_id", "error"),
    [
        pytest.param("L001", "Erreur : emprunt deja rendu", id="deja_rendu"),
        pytest.param("L999", "Erreur : emprunt inconnu", id="emprunt_inconnu"),
    ],
)
def test_invalid_return_is_rejected(library, capsys, loan_id, error):
    library.return_loan(loan_id)

    assert error in capsys.readouterr().out


def test_report_summarises_loans_and_fees(library, capsys):
    library.report()

    out = capsys.readouterr().out
    assert "Emprunts : 12 au total, 8 en cours, 4 en retard" in out
    assert "Penalites encaissees : 11.50 EUR" in out
    assert "Penalites en attente : 14.30 EUR" in out
    assert "1. Dune (3)" in out


def test_overdue_prints_reminders_and_total(library, capsys):
    library.overdue()

    out = capsys.readouterr().out
    assert out.count("EMAIL -> ") == 4
    assert "Total des penalites en cours : 14.30 EUR" in out


def test_export_writes_one_line_per_loan(library, tmp_path, capsys):
    target = tmp_path / "export.csv"

    library.export(str(target))

    lines = Path(target).read_text(encoding="utf-8").splitlines()
    assert lines[0] == "loan_id;member;title;start;due;returned;days_late;fee"
    assert len(lines) == 1 + len(library.loans)
    assert "L003;Bruno Lefevre;Fondation;2026-09-15;2026-10-06;;15;7.50" in lines
