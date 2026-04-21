# ABOUTME: Plan view custom route 测试
# ABOUTME: 覆盖 build_plan_view_payload 纯函数分支与 /plan-view/{user_id} endpoint 行为

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from langgraph.store.memory import InMemoryStore
from starlette.testclient import TestClient

from voliti.contracts.plan import PlanDocument
from voliti.http_app import (
    _parse_lifesigns,
    _parse_markers,
    app,
    build_plan_view_payload,
)
from voliti.store_contract import (
    COPING_PLANS_INDEX_KEY,
    PLAN_CURRENT_KEY,
    TIMELINE_MARKERS_KEY,
    make_file_value,
    make_user_namespace,
    unwrap_file_value,
)

FIXTURES_DIR = (
    Path(__file__).resolve().parents[2] / "tests" / "contracts" / "fixtures" / "store"
)
TEST_USER_ID = "http_test_0001"
USER_NS = make_user_namespace(TEST_USER_ID)


def _load_plan_fixture_raw() -> dict[str, Any]:
    return json.loads((FIXTURES_DIR / "plan_current.value.json").read_text(encoding="utf-8"))


def _load_plan_document() -> PlanDocument:
    raw = _load_plan_fixture_raw()
    return PlanDocument.model_validate_json(unwrap_file_value(raw))


def _make_markers_value(markers: list[dict[str, Any]]) -> dict[str, Any]:
    return make_file_value(json.dumps({"markers": markers}))


def _make_lifesigns_index_value(lines: list[str]) -> dict[str, Any]:
    return make_file_value("\n".join(["# LifeSign Index", *lines]))


# ── build_plan_view_payload ────────────────────────────────────────────


def test_build_plan_view_payload_returns_none_when_plan_absent() -> None:
    store = InMemoryStore()
    result = build_plan_view_payload(store, TEST_USER_ID, date(2026, 4, 20))
    assert result is None


def test_build_plan_view_payload_returns_plan_and_view_in_chapter() -> None:
    store = InMemoryStore()
    store.put(USER_NS, PLAN_CURRENT_KEY, _load_plan_fixture_raw())
    plan = _load_plan_document()

    result = build_plan_view_payload(store, TEST_USER_ID, date(2026, 4, 20))

    assert result is not None
    assert result["plan"]["plan_id"] == plan.plan_id
    assert result["plan"]["version"] == 1
    assert result["plan_view"]["plan_phase"] == "in_chapter"
    assert result["plan_view"]["active_chapter_index"] == 1


def test_build_plan_view_payload_before_start() -> None:
    store = InMemoryStore()
    store.put(USER_NS, PLAN_CURRENT_KEY, _load_plan_fixture_raw())

    result = build_plan_view_payload(store, TEST_USER_ID, date(2026, 3, 1))
    assert result is not None
    assert result["plan_view"]["plan_phase"] == "before_start"
    assert result["plan_view"]["active_chapter_index"] is None


def test_build_plan_view_payload_after_end() -> None:
    store = InMemoryStore()
    store.put(USER_NS, PLAN_CURRENT_KEY, _load_plan_fixture_raw())

    result = build_plan_view_payload(store, TEST_USER_ID, date(2026, 7, 1))
    assert result is not None
    assert result["plan_view"]["plan_phase"] == "after_end"


def test_build_plan_view_payload_includes_markers_batch() -> None:
    store = InMemoryStore()
    store.put(USER_NS, PLAN_CURRENT_KEY, _load_plan_fixture_raw())
    store.put(
        USER_NS,
        TIMELINE_MARKERS_KEY,
        _make_markers_value(
            [
                {
                    "id": "mk_extra",
                    "date": "2026-04-25T00:00:00+08:00",
                    "description": "体检预约",
                    "risk_level": "low",
                    "status": "upcoming",
                    "created_at": "2026-04-18T09:00:00Z",
                }
            ]
        ),
    )

    result = build_plan_view_payload(store, TEST_USER_ID, date(2026, 4, 20))
    assert result is not None
    # fixture plan 的 linked_markers 为空，watch_list 来自 linked_markers 过滤后为空；
    # 但 markers batch 读取流程仍应完成，不应抛错
    assert "watch_list" in result["plan_view"]


def test_build_plan_view_payload_survives_corrupted_markers() -> None:
    store = InMemoryStore()
    store.put(USER_NS, PLAN_CURRENT_KEY, _load_plan_fixture_raw())
    store.put(
        USER_NS,
        TIMELINE_MARKERS_KEY,
        {"version": "1", "content": ["{broken"], "created_at": "", "modified_at": ""},
    )

    result = build_plan_view_payload(store, TEST_USER_ID, date(2026, 4, 20))
    assert result is not None
    assert result["plan_view"]["plan_phase"] == "in_chapter"


# ── _parse_markers / _parse_lifesigns ─────────────────────────────────


def test_parse_markers_returns_empty_for_none() -> None:
    assert _parse_markers(None) == {}


def test_parse_markers_parses_valid_record() -> None:
    raw = _make_markers_value(
        [
            {
                "id": "mk_001",
                "date": "2026-04-20T00:00:00+08:00",
                "description": "出差上海",
                "risk_level": "high",
                "status": "upcoming",
                "created_at": "2026-04-19T10:00:00Z",
            }
        ]
    )
    result = _parse_markers(raw)
    assert "mk_001" in result
    assert result["mk_001"].risk_level == "high"


def test_parse_markers_degrades_on_malformed_envelope() -> None:
    assert _parse_markers({"content": "not a list"}) == {}


def test_parse_lifesigns_returns_empty_for_none() -> None:
    assert _parse_lifesigns(None) == {}


def test_parse_lifesigns_extracts_trigger_from_index_lines() -> None:
    raw = _make_lifesigns_index_value(
        [
            '- ls_001: "下班后压力大" → 泡茶+阳台3分钟 [active]',
            '- ls_002: "周末聚餐" → 提前吃轻食垫底 [active]',
        ]
    )
    result = _parse_lifesigns(raw)
    assert result == {
        "ls_001": {"trigger": "下班后压力大"},
        "ls_002": {"trigger": "周末聚餐"},
    }


def test_parse_lifesigns_ignores_malformed_lines() -> None:
    raw = _make_lifesigns_index_value(
        [
            "(not a list item)",
            "- ls_003: no_quote_trigger",
            '- ls_004: "只有一个引号',
        ]
    )
    result = _parse_lifesigns(raw)
    # ls_003 / ls_004 允许进入但 trigger 为空
    assert "ls_003" in result and result["ls_003"]["trigger"] == ""
    assert "ls_004" in result and result["ls_004"]["trigger"] == ""


# ── /plan-view/{user_id} endpoint ─────────────────────────────────────


@pytest.fixture
def store_with_plan() -> InMemoryStore:
    store = InMemoryStore()
    store.put(USER_NS, PLAN_CURRENT_KEY, _load_plan_fixture_raw())
    return store


@pytest.fixture
def client_with_store(
    store_with_plan: InMemoryStore, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    async def _fake_resolve_store() -> InMemoryStore:
        return store_with_plan

    monkeypatch.setattr("voliti.http_app._resolve_store", _fake_resolve_store)
    return TestClient(app)


def test_endpoint_rejects_invalid_user_id(client_with_store: TestClient) -> None:
    response = client_with_store.get("/plan-view/bad")
    assert response.status_code == 400


def test_endpoint_rejects_malformed_today_query(client_with_store: TestClient) -> None:
    response = client_with_store.get(f"/plan-view/{TEST_USER_ID}?today=not-a-date")
    assert response.status_code == 400


def test_endpoint_returns_payload_on_valid_request(client_with_store: TestClient) -> None:
    response = client_with_store.get(f"/plan-view/{TEST_USER_ID}?today=2026-04-20")
    assert response.status_code == 200
    body = response.json()
    assert body["plan"]["plan_id"] == "plan_fixture_001"
    assert body["plan_view"]["plan_phase"] == "in_chapter"


def test_endpoint_returns_404_when_plan_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    empty_store = InMemoryStore()

    async def _fake() -> InMemoryStore:
        return empty_store

    monkeypatch.setattr("voliti.http_app._resolve_store", _fake)
    client = TestClient(app)
    response = client.get(f"/plan-view/{TEST_USER_ID}")
    assert response.status_code == 404
