# ABOUTME: Store 契约与用户标识校验测试
# ABOUTME: 验证 user_id、namespace、文件封装值与强格式路径的 Pydantic 契约遵循运行时约定

import json
from pathlib import Path
from typing import Any

import pytest
from langgraph.store.memory import InMemoryStore
from pydantic import BaseModel, ValidationError

from voliti.contracts import (
    DashboardConfigRecord,
    MarkersRecord,
)
from voliti.contracts.plan import PlanDocument
from voliti.store_contract import (
    BRIEFING_FILE_PATH,
    BRIEFING_STORE_KEY,
    CONVERSATION_ARCHIVE_PREFIX,
    DAY_SUMMARY_PREFIX,
    InvalidStoreValueError,
    InvalidUserIDError,
    PLAN_CURRENT_KEY,
    PROFILE_CONTEXT_KEY,
    PROFILE_DASHBOARD_CONFIG_KEY,
    TIMELINE_MARKERS_KEY,
    make_file_value,
    make_interventions_namespace,
    make_user_namespace,
    parse_json_file_value,
    resolve_user_namespace,
    store_read_validated,
    store_write_validated,
    unwrap_file_value,
    validate_user_id,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "contracts" / "fixtures" / "store"


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def test_validate_user_id_accepts_eval_style_identifier() -> None:
    assert validate_user_id("eval_0001") == "eval_0001"


@pytest.mark.parametrize("user_id", ["", " user_0001 ", "abc", "bad/user", "bad user"])
def test_validate_user_id_rejects_invalid_value(user_id: str) -> None:
    with pytest.raises(InvalidUserIDError):
        validate_user_id(user_id)


def test_make_user_namespace_uses_validated_user_id() -> None:
    assert make_user_namespace("device_1234") == ("voliti", "device_1234")


def test_make_interventions_namespace_uses_validated_user_id() -> None:
    assert make_interventions_namespace("device_1234") == (
        "voliti",
        "device_1234",
        "interventions",
    )


def test_resolve_user_namespace_raises_without_user_id() -> None:
    with pytest.raises(InvalidUserIDError):
        resolve_user_namespace({"configurable": {}})


def test_resolve_user_namespace_raises_on_invalid_user_id() -> None:
    with pytest.raises(InvalidUserIDError):
        resolve_user_namespace({"configurable": {"user_id": "bad/user"}})


def test_make_file_value_round_trip() -> None:
    value = make_file_value('line1\n{"a":1}')
    assert unwrap_file_value(value) == 'line1\n{"a":1}'
    assert value["version"] == "1"


def test_parse_json_file_value_reads_wrapped_json() -> None:
    value = make_file_value('{"status":"ok","count":2}')
    assert parse_json_file_value(value) == {"status": "ok", "count": 2}


def test_unwrap_file_value_rejects_non_list_content() -> None:
    with pytest.raises(InvalidStoreValueError):
        unwrap_file_value({"content": "plain string"})


def test_store_keys_are_stable() -> None:
    assert PROFILE_CONTEXT_KEY == "/profile/context.md"
    assert PROFILE_DASHBOARD_CONFIG_KEY == "/profile/dashboardConfig"
    assert PLAN_CURRENT_KEY == "/plan/current.json"
    assert BRIEFING_STORE_KEY == "/derived/briefing.md"
    assert DAY_SUMMARY_PREFIX == "/day_summary/"
    assert CONVERSATION_ARCHIVE_PREFIX == "/conversation_archive/"


def test_briefing_file_path_uses_agent_vfs_prefix() -> None:
    assert BRIEFING_FILE_PATH == "/user/derived/briefing.md"


def test_shared_profile_fixture_round_trip() -> None:
    fixture = FIXTURES_DIR / "profile_context.value.json"
    value = json.loads(fixture.read_text(encoding="utf-8"))
    content = unwrap_file_value(value)
    assert "# User Profile" in content
    assert "onboarding_complete: true" in content


# ── 契约模型正向测试 ─────────────────────────────────────────────────────────


def _valid_dashboard_dict() -> dict[str, Any]:
    return {
        "north_star": {"key": "weight_trend", "label": "体重趋势", "type": "numeric"},
        "support_metrics": [
            {"key": "protein_days", "label": "达标天", "type": "count"}
        ],
    }


def test_dashboard_config_record_accepts_valid_data() -> None:
    record = DashboardConfigRecord.model_validate(_valid_dashboard_dict())
    assert record.north_star.key == "weight_trend"


def test_markers_record_accepts_valid_data() -> None:
    data = {
        "markers": [
            {
                "id": "mk_001",
                "date": "2026-04-20T00:00:00+08:00",
                "description": "出差上海",
                "risk_level": "high",
                "status": "upcoming",
                "created_at": "2026-04-19T10:00:00Z",
            }
        ]
    }
    record = MarkersRecord.model_validate(data)
    assert record.markers[0].risk_level == "high"


# ── 契约模型负向测试 ─────────────────────────────────────────────────────────


def test_dashboard_config_record_rejects_missing_north_star() -> None:
    data = _valid_dashboard_dict()
    data.pop("north_star")
    with pytest.raises(ValidationError):
        DashboardConfigRecord.model_validate(data)


def test_dashboard_config_record_rejects_support_metrics_not_list() -> None:
    data = _valid_dashboard_dict()
    data["support_metrics"] = "not_a_list"
    with pytest.raises(ValidationError):
        DashboardConfigRecord.model_validate(data)


def test_markers_record_rejects_invalid_risk_level() -> None:
    data = {
        "markers": [
            {
                "id": "mk_001",
                "date": "2026-04-20T00:00:00+08:00",
                "description": "出差上海",
                "risk_level": "extreme",
                "status": "upcoming",
                "created_at": "2026-04-19T10:00:00Z",
            }
        ]
    }
    with pytest.raises(ValidationError):
        MarkersRecord.model_validate(data)


# ── store_write_validated 行为测试 ───────────────────────────────────────────


def test_store_write_validated_writes_on_valid_data() -> None:
    store = InMemoryStore()
    namespace = ("voliti", "user_00001")
    ok, msg = store_write_validated(
        store,
        namespace,
        PROFILE_DASHBOARD_CONFIG_KEY,
        _valid_dashboard_dict(),
        DashboardConfigRecord,
    )
    assert ok is True
    assert msg == ""
    item = store.get(namespace, PROFILE_DASHBOARD_CONFIG_KEY)
    assert item is not None
    parsed = parse_json_file_value(item.value)
    assert parsed["north_star"]["key"] == "weight_trend"


def test_store_write_validated_does_not_write_on_invalid_data() -> None:
    store = InMemoryStore()
    namespace = ("voliti", "user_00001")
    data = _valid_dashboard_dict()
    data.pop("north_star")
    ok, msg = store_write_validated(
        store,
        namespace,
        PROFILE_DASHBOARD_CONFIG_KEY,
        data,
        DashboardConfigRecord,
    )
    assert ok is False
    assert len(msg) > 10
    assert store.get(namespace, PROFILE_DASHBOARD_CONFIG_KEY) is None


def test_store_write_validated_error_message_contains_field_and_example() -> None:
    store = InMemoryStore()
    namespace = ("voliti", "user_00001")
    data = _valid_dashboard_dict()
    data.pop("north_star")
    ok, msg = store_write_validated(
        store,
        namespace,
        PROFILE_DASHBOARD_CONFIG_KEY,
        data,
        DashboardConfigRecord,
    )
    assert ok is False
    assert "north_star" in msg
    assert "最小合法格式参考" in msg
    assert "DashboardConfigRecord" in msg


def test_store_write_validated_rejects_completely_empty_dict() -> None:
    store = InMemoryStore()
    namespace = ("voliti", "user_00001")
    ok, msg = store_write_validated(
        store,
        namespace,
        PROFILE_DASHBOARD_CONFIG_KEY,
        {},
        DashboardConfigRecord,
    )
    assert ok is False
    assert isinstance(msg, str) and len(msg) > 10


# ── store_read_validated 行为测试 ────────────────────────────────────────────


def test_store_read_validated_returns_none_when_key_absent() -> None:
    assert (
        store_read_validated(None, DashboardConfigRecord, PROFILE_DASHBOARD_CONFIG_KEY)
        is None
    )


def test_store_read_validated_returns_model_on_valid_data() -> None:
    raw = _load_fixture("dashboard_config.value.json")
    result = store_read_validated(
        raw, DashboardConfigRecord, PROFILE_DASHBOARD_CONFIG_KEY
    )
    assert isinstance(result, DashboardConfigRecord)
    assert result.north_star.key


def test_store_read_validated_raises_on_malformed_json() -> None:
    corrupted = {
        "version": "1",
        "content": ["{not valid json"],
        "created_at": "2026-04-19T00:00:00Z",
        "modified_at": "2026-04-19T00:00:00Z",
    }
    with pytest.raises(InvalidStoreValueError):
        store_read_validated(
            corrupted, DashboardConfigRecord, PROFILE_DASHBOARD_CONFIG_KEY
        )


def test_store_read_validated_raises_on_schema_violation() -> None:
    data = _valid_dashboard_dict()
    data.pop("north_star")
    raw = make_file_value(json.dumps(data))
    with pytest.raises(InvalidStoreValueError):
        store_read_validated(
            raw, DashboardConfigRecord, PROFILE_DASHBOARD_CONFIG_KEY
        )


def test_store_read_validated_raises_on_malformed_envelope() -> None:
    raw = {"content": "not a list"}
    with pytest.raises(InvalidStoreValueError):
        store_read_validated(
            raw, DashboardConfigRecord, PROFILE_DASHBOARD_CONFIG_KEY
        )


def test_store_read_validated_error_message_contains_store_key() -> None:
    raw = make_file_value(json.dumps({"support_metrics": []}))
    with pytest.raises(InvalidStoreValueError, match=PROFILE_DASHBOARD_CONFIG_KEY):
        store_read_validated(
            raw, DashboardConfigRecord, PROFILE_DASHBOARD_CONFIG_KEY
        )


# ── Fixture ↔ Pydantic 同步测试 ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "fixture_name,model_class,store_key",
    [
        ("plan_current.value.json", PlanDocument, PLAN_CURRENT_KEY),
        ("markers.value.json", MarkersRecord, TIMELINE_MARKERS_KEY),
        (
            "dashboard_config.value.json",
            DashboardConfigRecord,
            PROFILE_DASHBOARD_CONFIG_KEY,
        ),
    ],
)
def test_fixture_passes_contract_model(
    fixture_name: str,
    model_class: type[BaseModel],
    store_key: str,
) -> None:
    """所有强格式 fixture 必须与对应 Pydantic 模型保持同步。

    Fixture 更新或模型演进时此测试会失败，强制同步更新。
    """
    raw = _load_fixture(fixture_name)
    result = store_read_validated(raw, model_class, store_key)
    assert isinstance(result, model_class)
