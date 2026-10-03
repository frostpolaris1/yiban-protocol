"""Shared test helpers.

Tests are offline by construction: they only read the frozen gold fixtures under
``tests/fixtures/`` (never modified) and never touch the network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def _read_json(name: str):
    return json.loads(_read(name))


@pytest.fixture(scope="session")
def read_fixture():
    """Return a callable reading a fixture as text (UTF-8)."""
    return _read


@pytest.fixture(scope="session")
def read_fixture_json():
    """Return a callable reading and JSON-decoding a fixture."""
    return _read_json
