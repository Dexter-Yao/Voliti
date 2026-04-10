# ABOUTME: 语义记忆路径分类辅助函数
# ABOUTME: 定义长期语义记忆的权威写入范围与候选信号边界

from __future__ import annotations

import re
from typing import Literal

from voliti.store_contract import (
    CHAPTER_CURRENT_KEY,
    COACH_MEMORY_KEY,
    COPING_PLANS_INDEX_KEY,
    PROFILE_CONTEXT_KEY,
    PROFILE_DASHBOARD_CONFIG_KEY,
    TIMELINE_MARKERS_KEY,
)

SemanticMemoryPathClass = Literal["authoritative", "candidate", "non_semantic"]

_AUTHORITATIVE_PATHS = frozenset(
    {
        PROFILE_CONTEXT_KEY,
        PROFILE_DASHBOARD_CONFIG_KEY,
        CHAPTER_CURRENT_KEY,
        COPING_PLANS_INDEX_KEY,
        TIMELINE_MARKERS_KEY,
        COACH_MEMORY_KEY,
    }
)
_CHAPTER_ARCHIVE_PATTERN = re.compile(r"^/chapter/archive/[^/]+\.json$")
_COPING_PLAN_PATTERN = re.compile(r"^/coping_plans/[^/]+\.json$")
_CANDIDATE_SIGNAL_PREFIXES = (
    "/derived/",
)


def classify_semantic_memory_path(path: str) -> SemanticMemoryPathClass:
    """返回路径在语义记忆边界中的角色。"""
    if path in _AUTHORITATIVE_PATHS:
        return "authoritative"
    if _CHAPTER_ARCHIVE_PATTERN.fullmatch(path):
        return "authoritative"
    if _COPING_PLAN_PATTERN.fullmatch(path):
        return "authoritative"
    if path.startswith(_CANDIDATE_SIGNAL_PREFIXES):
        return "candidate"
    return "non_semantic"


def is_authoritative_semantic_memory_path(path: str) -> bool:
    """判断路径是否属于 Coach 可直接写入的权威语义记忆。"""
    return classify_semantic_memory_path(path) == "authoritative"
