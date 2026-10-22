import shutil
from datetime import date
from pathlib import Path

import pytest

import bibliotech

# Jeu de données dédié aux tests unitaires, indépendant de data/ (utilisé par l'appli)
DATA_DIR = Path(__file__).resolve().parent / "data"


@pytest.fixture
def library(tmp_path, monkeypatch):
    """Library sur une copie de tests/data/, au 21/10/2026."""
    data_dir = tmp_path / "data"
    shutil.copytree(DATA_DIR, data_dir)
    monkeypatch.setattr(bibliotech, "DATA", str(data_dir))
    monkeypatch.setattr(bibliotech, "TODAY", date(2026, 10, 21))
    return bibliotech.Library()
