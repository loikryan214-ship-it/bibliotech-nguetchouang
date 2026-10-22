"""Les tests unitaires ne touchent jamais aux vraies données (DATA et TODAY patchés)."""

from datetime import date
from pathlib import Path

import bibliotech

ROOT = Path(__file__).resolve().parent.parent
REAL_LOANS = ROOT / "data" / "loans.csv"
TEST_LOANS = ROOT / "tests" / "data" / "loans.csv"


def test_library_reads_the_patched_data_folder(library):
    assert library.find_book("B009") is not None
    assert library.find_member("M008") is not None


def test_get_today_returns_the_patched_date(library):
    assert bibliotech.get_today() == date(2026, 10, 21)


def test_borrow_writes_into_the_temporary_copy_only(library):
    real_before = REAL_LOANS.read_text(encoding="utf-8")
    test_before = TEST_LOANS.read_text(encoding="utf-8")

    library.borrow("M005", "B005")

    written = Path(bibliotech.DATA, "loans.csv").read_text(encoding="utf-8")
    assert "L013;M005;B005" in written
    assert REAL_LOANS.read_text(encoding="utf-8") == real_before
    assert TEST_LOANS.read_text(encoding="utf-8") == test_before
