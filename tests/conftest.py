"""Gemeinsame Vorbereitung der Testfaelle.

Legt die Modulpfade fuer die Hilfsmodule des Projekts fest und stellt die
geladene Signaldatenbank als Fixture bereit.
"""

from __future__ import annotations

import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for _path in (os.path.join(REPO_ROOT, "scripts"), os.path.join(REPO_ROOT, "amr", "scripts")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import can_model  # noqa: E402


@pytest.fixture(scope="session")
def dbc_path():
    """Pfad der Signaldatenbank."""
    return can_model.DBC_PATH


@pytest.fixture(scope="session")
def db(dbc_path):
    """Signaldatenbank, mit strenger Pruefung geladen (T-09 Schritt 1)."""
    return can_model.load_database(dbc_path)
