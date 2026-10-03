"""共享测试辅助。

测试天然离线：只读取 ``tests/fixtures/`` 下冻结的黄金夹具（绝不改动），不触网。
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
    """返回一个按 UTF-8 读取夹具文本的可调用对象。"""
    return _read


@pytest.fixture(scope="session")
def read_fixture_json():
    """返回一个读取并 JSON 解码夹具的可调用对象。"""
    return _read_json
