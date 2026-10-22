"""Tests unitaires de la lecture des dates (parse_date)."""

from datetime import date

import pytest

from bibliotech import parse_date


def test_parse_date_reads_iso_dates():
    assert parse_date("2026-10-21") == date(2026, 10, 21)


@pytest.mark.parametrize("text", ["2026-13-01", "2026-02-30", "21/10/2026", ""])
def test_parse_date_rejects_invalid_dates(text):
    with pytest.raises(ValueError):
        parse_date(text)
