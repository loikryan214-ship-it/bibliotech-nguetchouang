"""Tests unitaires de l'affichage des montants (format_eur)."""

import pytest

from bibliotech import format_eur


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        pytest.param(7.5, "7.50 EUR", id="deux_decimales"),
        pytest.param(0, "0.00 EUR", id="zero"),
        pytest.param(14.3, "14.30 EUR", id="arrondi_affiche"),
        pytest.param(0.30000000000000004, "0.30 EUR", id="bruit_flottant_masque"),
    ],
)
def test_format_eur_shows_two_decimals_and_currency(amount, expected):
    assert format_eur(amount) == expected
