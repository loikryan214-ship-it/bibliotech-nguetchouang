"""Tests unitaires des dataclasses Member et Loan."""

from pathlib import Path

from bibliotech import Loan, Member

DATA_DIR = Path(__file__).resolve().parent / "data"


def test_member_from_row_converts_active_flag():
    member = Member.from_row(
        ["M004", "David Moreau", "david.moreau@example.com", "standard", "0"]
    )

    assert member == Member(
        id="M004",
        name="David Moreau",
        email="david.moreau@example.com",
        type="standard",
        active=False,
    )


def test_library_loads_members_as_dataclasses(library):
    assert isinstance(library.find_member("M001"), Member)
    assert library.find_member("M001").active is True


def test_loan_from_row_reads_fee_and_defaults_to_zero():
    loan = Loan.from_row(["L003", "M002", "B003", "2026-09-15", "2026-10-06", "", ""])

    assert loan.member_id == "M002"
    assert loan.book_id == "B003"
    assert loan.returned == ""
    assert loan.fee == 0


def test_loan_to_row_keeps_csv_format(library):
    loan = library.find_loan("L002")

    assert loan.to_row() == "L002;M002;B005;2026-09-01;2026-09-08;2026-09-12;4.00"


def test_loan_from_row_then_to_row_gives_back_every_csv_line():
    lines = (DATA_DIR / "loans.csv").read_text(encoding="utf-8").splitlines()[1:]

    for line in lines:
        assert Loan.from_row(line.split(";")).to_row() == line
