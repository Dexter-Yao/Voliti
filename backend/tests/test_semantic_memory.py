# ABOUTME: 语义记忆路径分类测试
# ABOUTME: 验证 Coach 可直接写入的长期语义记忆范围与候选信号边界

from voliti.semantic_memory import (
    classify_semantic_memory_path,
    is_archive_source_path,
    is_authoritative_semantic_memory_path,
    is_candidate_signal_path,
    is_observability_only_path,
    is_runtime_only_path,
)
from voliti.store_contract import (
    CHAPTER_CURRENT_KEY,
    COACH_MEMORY_KEY,
    COPING_PLANS_INDEX_KEY,
    PROFILE_CONTEXT_KEY,
    PROFILE_DASHBOARD_CONFIG_KEY,
    TIMELINE_MARKERS_KEY,
)
from voliti.middleware.base import MemoryLifecycleMiddleware


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
    assert classify_semantic_memory_path("/derived/pattern_index.md") == "candidate_signal"
    assert (
        classify_semantic_memory_path("/derived/last_journey_analysis.json")
        == "candidate_signal"
    )
    assert is_candidate_signal_path("/user/derived/pattern_index.md")


def test_classify_semantic_memory_path_marks_archive_sources() -> None:
    assert classify_semantic_memory_path("/archive/conversations/2026-04-10/conv.json") == "archive_source"
    assert classify_semantic_memory_path("/user/archive/conversations/2026-04-10/conv.json") == "archive_source"
    assert is_archive_source_path("/archive/conversations/2026-04-10/conv.json")


def test_classify_semantic_memory_path_marks_runtime_only_paths() -> None:
    assert classify_semantic_memory_path("/ledger/2026-04-10/080000_observation.json") == "runtime_only"
    assert classify_semantic_memory_path("/user/ledger/2026-04-10/080000_observation.json") == "runtime_only"
    assert is_runtime_only_path("/ledger/2026-04-10/080000_observation.json")


def test_classify_semantic_memory_path_marks_observability_only_paths() -> None:
    assert classify_semantic_memory_path("/observability/traces/trace.json") == "observability_only"
    assert classify_semantic_memory_path("/user/observability/events/run.json") == "observability_only"
    assert is_observability_only_path("/observability/traces/trace.json")


def test_classify_semantic_memory_path_rejects_other_paths() -> None:
    assert classify_semantic_memory_path("/interventions/card_001") == "non_memory"
    assert classify_semantic_memory_path("/tmp/session_snapshot.json") == "non_memory"


def test_classify_semantic_memory_path_supports_user_prefixed_authoritative_paths() -> None:
    assert classify_semantic_memory_path("/user/profile/context.md") == "authoritative_semantic"
    assert classify_semantic_memory_path("/user/timeline/markers.json") == "authoritative_semantic"


def test_memory_lifecycle_rejects_archive_source_promotion() -> None:
    middleware = MemoryLifecycleMiddleware()
    assert middleware.can_promote(
        source_kind="archive_source",
        target_path=PROFILE_CONTEXT_KEY,
        source_name="conversation_archive",
        confirmed=True,
    ) is False


def test_memory_lifecycle_rejects_journey_analysis_promotion() -> None:
    middleware = MemoryLifecycleMiddleware()
    assert middleware.can_promote(
        source_kind="candidate_signal",
        target_path=PROFILE_CONTEXT_KEY,
        source_name="journey_analysis",
        confirmed=True,
    ) is False


def test_memory_lifecycle_rejects_runtime_and_observability_promotion() -> None:
    middleware = MemoryLifecycleMiddleware()
    assert middleware.can_promote(
        source_kind="runtime_only",
        target_path=PROFILE_CONTEXT_KEY,
        source_name="tool_capture",
        confirmed=True,
    ) is False
    assert middleware.can_promote(
        source_kind="observability_only",
        target_path=PROFILE_CONTEXT_KEY,
        source_name="trace",
        confirmed=True,
    ) is False


def test_memory_lifecycle_requires_authoritative_target_and_confirmation() -> None:
    middleware = MemoryLifecycleMiddleware()
    assert middleware.can_promote(
        source_kind="candidate_signal",
        target_path=PROFILE_CONTEXT_KEY,
        source_name="coach_confirmation",
        confirmed=False,
    ) is False
    assert middleware.can_promote(
        source_kind="candidate_signal",
        target_path="/derived/pattern_index.md",
        source_name="coach_confirmation",
        confirmed=True,
    ) is False
    assert middleware.can_promote(
        source_kind="candidate_signal",
        target_path=PROFILE_CONTEXT_KEY,
        source_name="coach_confirmation",
        confirmed=True,
    ) is True


def test_memory_lifecycle_wrap_tool_call_is_passthrough() -> None:
    middleware = MemoryLifecycleMiddleware()

    result = middleware.wrap_tool_call("request", lambda request: {"request": request})

    assert result == {"request": "request"}


def test_memory_lifecycle_after_model_and_after_agent_are_noops() -> None:
    middleware = MemoryLifecycleMiddleware()

    assert middleware.after_model(state={}, runtime=None) is None
    assert middleware.after_agent(state={}, runtime=None) is None
