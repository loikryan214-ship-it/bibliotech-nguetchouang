"""Tests de caractérisation (golden master) de BiblioTech.

Ces tests figent le comportement ACTUEL de l'application, vu de l'extérieur :
ils lancent la ligne de commande et comparent la sortie produite à des
résultats de référence enregistrés dans tests/golden/.

Ils ne dépendent pas de l'organisation interne du code. Vous pouvez donc
renommer, découper et réorganiser librement bibliotech.py : tant que ces
tests restent verts, le comportement est préservé.

Ne modifiez ni ce fichier ni les fichiers de tests/golden/.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
DEFAULT_TODAY = "2026-10-21"

# Chaque scénario : une suite de commandes, puis les fichiers à vérifier.
SCENARIOS = {
    "list": ([["list"]], []),
    "members": ([["members"]], []),
    "overdue": ([["overdue"]], []),
    "overdue_none": ([["overdue", "--today", "2026-08-01"]], []),
    "report": ([["report"]], []),
    "borrow_ok": ([["borrow", "M005", "B005"], ["list"]], ["loans.csv"]),
    "borrow_limit": (
        [
            ["borrow", "M005", "B005"],
            ["borrow", "M005", "B002"],
            ["borrow", "M005", "B007"],
        ],
        ["loans.csv"],
    ),
    "borrow_refused_late_member": ([["borrow", "M001", "B002"]], ["loans.csv"]),
    "borrow_refused_inactive_member": ([["borrow", "M004", "B002"]], []),
    "borrow_refused_unavailable": ([["borrow", "M005", "B003"]], []),
    "borrow_refused_already_borrowed": ([["borrow", "M005", "B001"]], []),
    "borrow_unknown": ([["borrow", "M999", "B001"], ["borrow", "M005", "B999"]], []),
    "borrow_usage": ([["borrow", "M005"]], []),
    "return_late_student_dvd": ([["return", "L004"], ["members"]], ["loans.csv"]),
    "return_on_time": ([["return", "L006"]], ["loans.csv"]),
    "return_fee_capped": ([["return", "L003", "--today", "2026-12-31"]], ["loans.csv"]),
    "return_errors": ([["return", "L001"], ["return", "L999"], ["return"]], []),
    "report_after_returns": ([["return", "L004"], ["return", "L003"], ["report"]], []),
    "export": ([["export", "export.csv"]], ["export.csv"]),
    "unknown_command": ([["fly"]], []),
    "no_command": ([[]], []),
}


@pytest.fixture
def workspace(tmp_path):
    """Copie des données d'exemple dans un dossier temporaire."""
    data_dir = tmp_path / "data"
    shutil.copytree(ROOT / "data", data_dir)
    return tmp_path


def run_scenario(workspace, commands, files):
    transcript = []
    for args in commands:
        full_args = list(args)
        if "--today" not in full_args:
            full_args += ["--today", DEFAULT_TODAY]
        result = subprocess.run(
            [sys.executable, str(ROOT / "bibliotech.py"), *full_args],
            cwd=workspace,
            env={**os.environ, "BIBLIOTECH_DATA": str(workspace / "data")},
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        transcript.append("$ bibliotech " + " ".join(full_args))
        transcript.append(result.stdout.rstrip("\n"))
        transcript.append(f"[code de sortie : {result.returncode}]")
    for name in files:
        path = workspace / "data" / name
        if not path.exists():
            path = workspace / name
        transcript.append(f"--- {name} ---")
        transcript.append(path.read_text(encoding="utf-8").rstrip("\n"))
    return "\n".join(transcript) + "\n"


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_behaviour_is_unchanged(name, workspace):
    commands, files = SCENARIOS[name]
    actual = run_scenario(workspace, commands, files)
    expected = (GOLDEN_DIR / f"{name}.txt").read_text(encoding="utf-8")
    assert actual == expected
