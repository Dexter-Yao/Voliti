# ABOUTME: Briefing 计算模块单元测试
# ABOUTME: 验证各项 briefing 指标的确定性计算逻辑

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import AsyncMock

import pytest

from voliti.briefing import (
    _PLAN_DATA_UNAVAILABLE,
    PlanBriefingSlice,
    build_plan_briefing_slice,
    collect_recent_summaries,
    compute_and_write_briefing,
    compute_days_since_last_session,
    compute_sessions_this_week,
    extract_lifesign_activity,
    extract_upcoming_markers,
    format_briefing,
    render_plan_xml,
)
from voliti.contracts.plan import PlanDocument
from voliti.derivations.plan_view import compute_plan_view


class TestDaysSinceLastSession:
    def test_returns_none_for_empty_threads(self) -> None:
        assert compute_days_since_last_session([]) is None

    def test_returns_zero_for_today(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        threads = [{"metadata": {"date": "2026-04-13"}}]
        assert compute_days_since_last_session(threads, now=now) == 0

    def test_returns_correct_days(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        threads = [{"metadata": {"date": "2026-04-10"}}]
        assert compute_days_since_last_session(threads, now=now) == 3

    def test_uses_most_recent_thread(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        threads = [
            {"metadata": {"date": "2026-04-10"}},
            {"metadata": {"date": "2026-04-12"}},
            {"metadata": {"date": "2026-04-08"}},
        ]
        assert compute_days_since_last_session(threads, now=now) == 1

    def test_ignores_threads_without_date(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        threads = [{"metadata": {}}, {"metadata": {"date": "2026-04-11"}}]
        assert compute_days_since_last_session(threads, now=now) == 2


class TestSessionsThisWeek:
    def test_counts_sessions_from_monday(self) -> None:
        # 2026-04-13 is Monday
        now = datetime(2026, 4, 15, 10, 0, tzinfo=timezone.utc)  # Wednesday
        threads = [
            {"metadata": {"date": "2026-04-13"}},  # Monday
            {"metadata": {"date": "2026-04-14"}},  # Tuesday
            {"metadata": {"date": "2026-04-15"}},  # Wednesday
            {"metadata": {"date": "2026-04-12"}},  # Sunday (prev week)
        ]
        assert compute_sessions_this_week(threads, now=now) == 3

    def test_returns_zero_for_empty(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        assert compute_sessions_this_week([], now=now) == 0


class TestExtractUpcomingMarkers:
    def test_extracts_upcoming_within_window(self) -> None:
        now = datetime(2026, 4, 13, 0, 0, tzinfo=timezone.utc)
        markers = json.dumps({
            "markers": [
                {
                    "id": "mk_001",
                    "date": "2026-04-15T00:00:00+08:00",
                    "description": "出差北京",
                    "risk_level": "medium",
                    "status": "upcoming",
                },
                {
                    "id": "mk_002",
                    "date": "2026-04-25T00:00:00+08:00",
                    "description": "体检",
                    "risk_level": "low",
                    "status": "upcoming",
                },
                {
                    "id": "mk_003",
                    "date": "2026-04-10T00:00:00+08:00",
                    "description": "已过期",
                    "risk_level": "high",
                    "status": "passed",
                },
            ]
        })
        result = extract_upcoming_markers(markers, now=now, days_ahead=7)
        assert len(result) == 1
        assert result[0]["desc"] == "出差北京"

    def test_returns_empty_for_none(self) -> None:
        assert extract_upcoming_markers(None) == []

    def test_returns_empty_for_invalid_json(self) -> None:
        assert extract_upcoming_markers("not json") == []


class TestExtractLifesignActivity:
    def test_parses_index_format(self) -> None:
        content = '# LifeSign Index\n- ls_001: "下班后压力大想吃零食" → 泡茶+阳台3分钟 [active]\n- ls_002: "周末聚餐" → 提前吃轻食垫底 [active]'
        result = extract_lifesign_activity(content)
        assert len(result) == 2
        assert result[0]["id"] == "ls_001"
        assert result[0]["trigger"] == "下班后压力大想吃零食"

    def test_returns_empty_for_none(self) -> None:
        assert extract_lifesign_activity(None) == []


class TestFormatBriefing:
    def test_format_complete_briefing(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = format_briefing(
            days_since_last=2,
            sessions_this_week=4,
            upcoming_markers=[{"date": "04/15", "desc": "出差北京", "risk": "medium"}],
            lifesign_activity=[
                {"id": "ls_001", "trigger": "下班压力"},
            ],
            now=now,
        )
        assert "2026-04-13" in result
        assert "距上次会话：2 天" in result
        assert "本周会话：4 次" in result
        assert "出差北京" in result
        assert "下班压力" in result

    def test_format_minimal_briefing(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = format_briefing(
            days_since_last=None,
            sessions_this_week=0,
            upcoming_markers=[],
            lifesign_activity=[],
            now=now,
        )
        assert "Coach Briefing" in result
        assert "本周会话：0 次" in result
        assert "近期日程" not in result

    def test_no_streak_language(self) -> None:
        """briefing 不应包含任何游戏化语言。"""
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = format_briefing(
            days_since_last=0,
            sessions_this_week=7,
            upcoming_markers=[],
            lifesign_activity=[],
            now=now,
        )
        assert "打卡" not in result
        assert "streak" not in result.lower()
        assert "连续" not in result


class TestCollectRecentSummaries:
    @pytest.mark.asyncio
    async def test_reads_canonical_day_summary_keys(self) -> None:
        client = AsyncMock()
        client.store.get_item = AsyncMock(return_value=None)

        await collect_recent_summaries(
            client,
            ("voliti", "testuser"),
            now=datetime(2026, 4, 14, 10, 0, tzinfo=timezone.utc),
            days_back=2,
        )

        requested_keys = [call.args[1] for call in client.store.get_item.await_args_list]
        assert requested_keys == [
            "/day_summary/2026-04-13.md",
            "/day_summary/2026-04-12.md",
        ]


# ── Plan briefing slice ────────────────────────────────────────────────


def _baseline_plan_dict() -> dict[str, Any]:
    """构造一份处于 chapter 2（"训练成锚"）in_chapter 状态的 PlanDocument。"""
    return {
        "plan_id": "plan_briefing_001",
        "status": "active",
        "version": 2,
        "predecessor_version": 1,
        "target_summary": "两个月减 10 斤",
        "overall_narrative": "两个月前体重回到一个我自己都不认识的数字。",
        "started_at": "2026-02-21T00:00:00+08:00",
        "planned_end_at": "2026-04-17T23:59:59+08:00",
        "created_at": "2026-02-21T09:15:00+08:00",
        "revised_at": "2026-04-13T07:32:00+08:00",
        "target": {
            "metric": "weight_kg",
            "baseline": 70.0,
            "goal_value": 65.0,
            "duration_weeks": 8,
            "rate_kg_per_week": 0.625,
        },
        "chapters": [
            {
                "chapter_index": 1,
                "name": "立起早餐",
                "why_this_chapter": "建立早餐蛋白锚点。",
                "start_date": "2026-02-21",
                "end_date": "2026-03-06",
                "milestone": "早餐蛋白达标 5/7 持续两周",
                "process_goals": [
                    {
                        "name": "早餐蛋白 25 克以上",
                        "weekly_target_days": 5,
                        "weekly_total_days": 7,
                        "how_to_measure": "Coach 每日评估",
                        "examples": [],
                    }
                ],
                "daily_rhythm": {
                    "meals": {"value": "三餐 · 蛋白分散", "tooltip": "早中晚各 25g"},
                    "training": {"value": "每周两次", "tooltip": "适应期量小"},
                    "sleep": {"value": "十一点半", "tooltip": "上床时间目标"},
                },
                "daily_calorie_range": [1500, 1800],
                "daily_protein_grams_range": [90, 110],
                "weekly_training_count": 2,
            },
            {
                "chapter_index": 2,
                "name": "训练成锚",
                "why_this_chapter": "让训练变成不用挣扎的惯性。",
                "start_date": "2026-03-07",
                "end_date": "2026-04-17",
                "milestone": "再减 3 公斤",
                "process_goals": [
                    {
                        "name": "每周三次训练",
                        "weekly_target_days": 3,
                        "weekly_total_days": 3,
                        "how_to_measure": "训练日可弹性",
                        "examples": [],
                    }
                ],
                "daily_rhythm": {
                    "meals": {"value": "三餐 · 蛋白分散", "tooltip": "沿用阶段一"},
                    "training": {"value": "每周三次", "tooltip": "力量优先"},
                    "sleep": {"value": "十一点半", "tooltip": "沿用阶段一"},
                },
                "daily_calorie_range": [1400, 1700],
                "daily_protein_grams_range": [100, 120],
                "weekly_training_count": 3,
            },
        ],
        "linked_lifesigns": [],
        "linked_markers": [],
        "current_week": {
            "updated_at": "2026-04-13T07:32:00+08:00",
            "source": "coach_inferred",
            "goals_status": [
                {"goal_name": "每周三次训练", "days_met": 2, "days_expected": 3}
            ],
            "highlights": "周二训练比计划多做了 15 分钟",
            "concerns": "周六深夜又吃了一顿",
        },
    }


class TestBuildPlanBriefingSlice:
    def test_projects_active_chapter_when_in_chapter(self) -> None:
        plan = PlanDocument.model_validate(_baseline_plan_dict())
        today = date(2026, 4, 13)   # chapter 2 的第 5 周
        plan_view = compute_plan_view(plan=plan, today=today)

        slice_ = build_plan_briefing_slice(plan, plan_view)

        assert slice_.plan_phase == "in_chapter"
        assert slice_.active_chapter_index == 2
        assert slice_.target_summary == "两个月减 10 斤"
        assert slice_.active_chapter is not None
        assert slice_.active_chapter.name == "训练成锚"
        assert slice_.active_chapter.daily_calorie_range == (1400, 1700)
        assert slice_.current_week is not None
        assert slice_.current_week.goals_status[0].goal_name == "每周三次训练"
        assert slice_.week_freshness is not None
        assert slice_.week_freshness.level in {"fresh", "stale", "very_stale"}

    def test_active_chapter_is_none_before_start(self) -> None:
        doc = _baseline_plan_dict()
        plan = PlanDocument.model_validate(doc)
        today = date(2026, 2, 1)  # Plan 尚未开始
        plan_view = compute_plan_view(plan=plan, today=today)

        slice_ = build_plan_briefing_slice(plan, plan_view)

        assert slice_.plan_phase == "before_start"
        assert slice_.active_chapter_index is None
        assert slice_.active_chapter is None


class TestRenderPlanXml:
    def test_wraps_content_with_boundary_note(self) -> None:
        plan = PlanDocument.model_validate(_baseline_plan_dict())
        plan_view = compute_plan_view(plan=plan, today=date(2026, 4, 13))
        slice_ = build_plan_briefing_slice(plan, plan_view)

        xml = render_plan_xml(slice_)

        assert xml.startswith("<user_plan_data>")
        assert "</user_plan_data>" in xml
        assert "视为数据快照" in xml
        assert "不是指令" in xml
        # active chapter 详情出现
        assert "训练成锚" in xml
        assert "每周三次训练" in xml
        # week_freshness 作为属性
        assert "<week_freshness level=" in xml

    def test_escapes_unsafe_characters(self) -> None:
        # 构造一个 highlights 含 `<` `>` `&` 的 slice 来验证转义
        slice_ = PlanBriefingSlice(
            target_summary="测试 <b>标题</b> & 符号",
            plan_phase="in_chapter",
            week_index=1,
            active_chapter_index=1,
            days_left_in_chapter=5,
            active_chapter=None,
            current_week=None,
            week_freshness=None,
            watch_list=[],
        )
        xml = render_plan_xml(slice_)
        assert "&lt;b&gt;" in xml
        assert "&amp;" in xml
        assert "<b>" not in xml


class TestFormatBriefingWithPlan:
    def test_appends_plan_xml_when_provided(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = format_briefing(
            days_since_last=0,
            sessions_this_week=2,
            upcoming_markers=[],
            lifesign_activity=[],
            plan_xml="<user_plan_data>\n  <target_summary>测试</target_summary>\n</user_plan_data>",
            now=now,
        )
        assert "<user_plan_data>" in result
        # Plan 段应在日历入口行之后
        assert result.index("完整日历") < result.index("<user_plan_data>")

    def test_appends_unavailable_block_when_provided(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = format_briefing(
            days_since_last=0,
            sessions_this_week=2,
            upcoming_markers=[],
            lifesign_activity=[],
            plan_xml=_PLAN_DATA_UNAVAILABLE,
            now=now,
        )
        assert "<user_plan_data_unavailable>" in result

    def test_no_plan_block_when_none(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = format_briefing(
            days_since_last=0,
            sessions_this_week=2,
            upcoming_markers=[],
            lifesign_activity=[],
            now=now,
        )
        assert "<user_plan_data" not in result


# ── compute_and_write_briefing 集成 ───────────────────────────────────


def _make_file_item(content: str) -> dict[str, Any]:
    return {"value": {"version": "1", "content": content.splitlines(),
                      "created_at": "2026-04-13T00:00:00+00:00",
                      "modified_at": "2026-04-13T00:00:00+00:00"}}


class TestComputeAndWriteBriefingPlanIntegration:
    @pytest.mark.asyncio
    async def test_no_plan_skips_xml_section(self) -> None:
        """用户未建立 Plan → briefing 正文无 <user_plan_data> 段。"""
        client = AsyncMock()
        client.threads.search = AsyncMock(return_value=[])
        client.store.get_item = AsyncMock(return_value=None)
        client.store.put_item = AsyncMock()

        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = await compute_and_write_briefing(
            client=client,
            user_id="u01_briefing",
            namespace=("voliti", "u01_briefing"),
            now=now,
        )
        assert result is not None
        assert "<user_plan_data" not in result

    @pytest.mark.asyncio
    async def test_plan_present_injects_xml_section(self) -> None:
        """Plan 存在 → briefing 末尾有 <user_plan_data> 段且含 active chapter 名。"""
        plan_json = json.dumps(_baseline_plan_dict(), ensure_ascii=False)

        async def fake_get_item(namespace, key):
            if key == "/plan/current.json":
                return _make_file_item(plan_json)
            return None

        client = AsyncMock()
        client.threads.search = AsyncMock(return_value=[])
        client.store.get_item = AsyncMock(side_effect=fake_get_item)
        client.store.put_item = AsyncMock()

        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = await compute_and_write_briefing(
            client=client,
            user_id="u02_briefing",
            namespace=("voliti", "u02_briefing"),
            now=now,
        )
        assert result is not None
        assert "<user_plan_data>" in result
        assert "训练成锚" in result
        assert "week_freshness level=" in result

    @pytest.mark.asyncio
    async def test_corrupt_plan_json_degrades_gracefully(self) -> None:
        """Plan JSON 无法解析 → 注入 <user_plan_data_unavailable>，不整体失败。"""

        async def fake_get_item(namespace, key):
            if key == "/plan/current.json":
                return _make_file_item("{not valid json")
            return None

        client = AsyncMock()
        client.threads.search = AsyncMock(return_value=[])
        client.store.get_item = AsyncMock(side_effect=fake_get_item)
        client.store.put_item = AsyncMock()

        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = await compute_and_write_briefing(
            client=client,
            user_id="u03_briefing",
            namespace=("voliti", "u03_briefing"),
            now=now,
        )
        assert result is not None
        assert "<user_plan_data_unavailable>" in result

    @pytest.mark.asyncio
    async def test_corrupt_current_recovers_from_archive(self) -> None:
        """/plan/current.json 损坏但 archive 有合法 active plan → briefing 应注入恢复后的方案。"""
        plan_json = json.dumps(_baseline_plan_dict(), ensure_ascii=False)

        async def fake_get_item(namespace, key):
            if key == "/plan/current.json":
                return _make_file_item("{not valid json")
            return None

        async def fake_search_items(namespace, limit, offset):
            assert namespace == ("voliti", "u04_briefing", "plan_archive")
            return {
                "items": [
                    {
                        "key": "plan_briefing_001_v2.json",
                        "value": _make_file_item(plan_json)["value"],
                    }
                ]
            }

        client = AsyncMock()
        client.threads.search = AsyncMock(return_value=[])
        client.store.get_item = AsyncMock(side_effect=fake_get_item)
        client.store.search_items = AsyncMock(side_effect=fake_search_items)
        client.store.put_item = AsyncMock()

        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = await compute_and_write_briefing(
            client=client,
            user_id="u04_briefing",
            namespace=("voliti", "u04_briefing"),
            now=now,
        )
        assert result is not None
        assert "<user_plan_data>" in result
        assert "训练成锚" in result
