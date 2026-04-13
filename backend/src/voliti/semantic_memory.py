# ABOUTME: 语义边界分类辅助函数
# ABOUTME: 定义长期语义、候选信号、archive 证据、运行时数据与可观测性数据的单一分类入口

from __future__ import annotations

import re
from typing import Literal

from voliti.store_contract import (
    CHAPTER_CURRENT_KEY,
    COACH_MEMORY_KEY,
    COPING_PLANS_INDEX_KEY,
    LIFESIGNS_KEY,
    PROFILE_CONTEXT_KEY,
    PROFILE_DASHBOARD_CONFIG_KEY,
    TIMELINE_CALENDAR_KEY,
    TIMELINE_MARKERS_KEY,
)

SemanticMemoryPathClass = Literal[
    "authoritative_semantic",
    "candidate_signal",
    "archive_source",
    "runtime_only",
    "observability_only",
    "non_memory",
]

_AUTHORITATIVE_PATHS = frozenset(
    {
        PROFILE_CONTEXT_KEY,
        PROFILE_DASHBOARD_CONFIG_KEY,
        CHAPTER_CURRENT_KEY,
        COPING_PLANS_INDEX_KEY,
        TIMELINE_MARKERS_KEY,
        COACH_MEMORY_KEY,
        LIFESIGNS_KEY,
        TIMELINE_CALENDAR_KEY,
    }
)
_CHAPTER_ARCHIVE_PATTERN = re.compile(r"^/chapter/archive/[^/]+\.json$")
_COPING_PLAN_PATTERN = re.compile(r"^/coping_plans/[^/]+\.json$")
_CANDIDATE_SIGNAL_PREFIXES = (
    "/derived/",
)
_ARCHIVE_SOURCE_PREFIXES = ("/archive/", "/day_summary/")
_RUNTIME_ONLY_PREFIXES = (
    "/ledger/",
)
_OBSERVABILITY_ONLY_PREFIXES = (
    "/observability/",
)


def _normalize_store_path(path: str) -> str:
    """将路径收敛为 backend 统一视角。"""
    if path.startswith("/user/"):
        return path[5:]
    return path


def classify_semantic_memory_path(path: str) -> SemanticMemoryPathClass:
    """返回路径在语义边界中的角色。"""
    normalized_path = _normalize_store_path(path)

    if normalized_path in _AUTHORITATIVE_PATHS:
        return "authoritative_semantic"
    if _CHAPTER_ARCHIVE_PATTERN.fullmatch(normalized_path):
        return "authoritative_semantic"
    if _COPING_PLAN_PATTERN.fullmatch(normalized_path):
        return "authoritative_semantic"
    if normalized_path.startswith(_CANDIDATE_SIGNAL_PREFIXES):
        return "candidate_signal"
    if normalized_path.startswith(_ARCHIVE_SOURCE_PREFIXES):
        return "archive_source"
    if normalized_path.startswith(_RUNTIME_ONLY_PREFIXES):
        return "runtime_only"
    if normalized_path.startswith(_OBSERVABILITY_ONLY_PREFIXES):
        return "observability_only"
    return "non_memory"


def is_authoritative_semantic_memory_path(path: str) -> bool:
    """判断路径是否属于 Coach 可直接写入的权威语义记忆。"""
    return classify_semantic_memory_path(path) == "authoritative_semantic"


def is_candidate_signal_path(path: str) -> bool:
    """判断路径是否属于候选信号。"""
    return classify_semantic_memory_path(path) == "candidate_signal"


def is_archive_source_path(path: str) -> bool:
    """判断路径是否属于 archive 原始证据。"""
    return classify_semantic_memory_path(path) == "archive_source"


def is_runtime_only_path(path: str) -> bool:
    """判断路径是否属于运行时原始数据。"""
    return classify_semantic_memory_path(path) == "runtime_only"


def is_observability_only_path(path: str) -> bool:
    """判断路径是否属于仅用于可观测性的记录。"""
    return classify_semantic_memory_path(path) == "observability_only"
