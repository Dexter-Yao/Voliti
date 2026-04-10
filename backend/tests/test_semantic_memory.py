# ABOUTME: 语义记忆路径分类测试
# ABOUTME: 验证 Coach 可直接写入的长期语义记忆范围与候选信号边界

from voliti.semantic_memory import (
    classify_semantic_memory_path,
    is_authoritative_semantic_memory_path,
)
from voliti.store_contract import (
    CHAPTER_CURRENT_KEY,
    COACH_MEMORY_KEY,
    COPING_PLANS_INDEX_KEY,
    PROFILE_CONTEXT_KEY,
    PROFILE_DASHBOARD_CONFIG_KEY,
    TIMELINE_MARKERS_KEY,
)


def test_authoritative_semantic_memory_paths_are_stable() -> None:
    assert is_authoritative_semantic_memory_path(PROFILE_CONTEXT_KEY)
    assert is_authoritative_semantic_memory_path(PROFILE_DASHBOARD_CONFIG_KEY)
    assert is_authoritative_semantic_memory_path(CHAPTER_CURRENT_KEY)
    assert is_authoritative_semantic_memory_path(COPING_PLANS_INDEX_KEY)
    assert is_authoritative_semantic_memory_path(TIMELINE_MARKERS_KEY)
    assert is_authoritative_semantic_memory_path(COACH_MEMORY_KEY)


def test_authoritative_semantic_memory_path_accepts_structured_entities() -> None:
    assert is_authoritative_semantic_memory_path("/chapter/archive/ch_001.json")
    assert is_authoritative_semantic_memory_path("/coping_plans/ls_001.json")


def test_classify_semantic_memory_path_marks_candidate_signals() -> None:
    assert classify_semantic_memory_path("/derived/pattern_index.md") == "candidate"
    assert (
        classify_semantic_memory_path("/derived/last_journey_analysis.json")
        == "candidate"
    )


def test_classify_semantic_memory_path_rejects_non_semantic_paths() -> None:
    assert classify_semantic_memory_path("/ledger/2026-04-10/080000_observation.json") == "non_semantic"
    assert classify_semantic_memory_path("/archive/conversations/2026-04-10/conv.json") == "non_semantic"
    assert classify_semantic_memory_path("/interventions/card_001") == "non_semantic"
