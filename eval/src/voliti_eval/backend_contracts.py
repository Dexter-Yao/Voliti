# ABOUTME: backend 真相源加载器
# ABOUTME: 从 monorepo 的 backend/src 动态加载运行时契约模块，避免在 eval 内复制常量

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_SRC = _ROOT / "backend" / "src"


def _ensure_backend_on_path() -> None:
    backend_src = str(_BACKEND_SRC)
    if backend_src not in sys.path:
        sys.path.insert(0, backend_src)


def get_store_contract_module():
    _ensure_backend_on_path()
    return importlib.import_module("voliti.store_contract")


def get_a2ui_module():
    _ensure_backend_on_path()
    return importlib.import_module("voliti.a2ui")


def get_experiential_module():
    _ensure_backend_on_path()
    return importlib.import_module("voliti.tools.experiential")


def get_plan_contract_module():
    _ensure_backend_on_path()
    return importlib.import_module("voliti.contracts.plan")
