"""Tests unitaires des options de la ligne de commande (parse_options, main)."""

from datetime import date

import pytest

import bibliotech


def test_parse_options_extracts_today_and_debug():
    args, today, debug = bibliotech.parse_options(
        ["list", "--today", "2026-10-21", "--debug"]
    )

    assert args == ["list"]
    assert today == date(2026, 10, 21)
    assert debug is True


@pytest.mark.parametrize(
    "argv",
    [
        pytest.param(["list", "--today"], id="date_absente"),
        pytest.param(["list", "--today", "2026-13-01"], id="mois_invalide"),
        pytest.param(["list", "--today", "21/10/2026"], id="mauvais_format"),
    ],
)
def test_invalid_today_option_prints_usage_error_instead_of_crashing(
    argv, capsys, monkeypatch
):
    monkeypatch.setattr(bibliotech, "TODAY", None)

    exit_code = bibliotech.main(argv)

    assert exit_code == bibliotech.EXIT_USAGE
    assert "--today attend une date au format AAAA-MM-JJ" in capsys.readouterr().out
