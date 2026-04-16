# ABOUTME: Briefing 计算模块单元测试
# ABOUTME: 验证各项 briefing 指标的确定性计算逻辑

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from voliti.briefing import (
    collect_recent_summaries,
    compute_days_since_last_session,
    compute_sessions_this_week,
    extract_goal_chapter_summary,
    extract_lifesign_activity,
    extract_upcoming_markers,
    format_briefing,
)


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


class TestExtractGoalChapterSummary:
    def test_normal_goal_and_chapter(self) -> None:
        goal = json.dumps({
            "description": "减重 10kg",
            "target_date": "2026-09-01T00:00:00Z",
        })
        chapter = json.dumps({
            "title": "建立基础",
            "milestone": "体重稳定在 75kg",
            "process_goals": [
                {"description": "每日步数", "target": "8000步"},
                {"description": "蛋白质摄入", "target": "120g"},
                {"description": "睡眠", "target": "7小时"},
            ],
        })
        result = extract_goal_chapter_summary(goal, chapter)
        assert result is not None
        assert "减重 10kg" in result
        assert "2026-09-01" in result
        assert "建立基础" in result
        assert "体重稳定在 75kg" in result
        assert "每日步数(8000步)" in result
        assert "蛋白质摄入(120g)" in result

    def test_invalid_json_returns_none(self) -> None:
        result = extract_goal_chapter_summary("not json", "{broken")
        assert result is None

    def test_both_none_returns_none(self) -> None:
        assert extract_goal_chapter_summary(None, None) is None

    def test_goal_only(self) -> None:
        goal = json.dumps({"description": "减重 5kg", "target_date": ""})
        result = extract_goal_chapter_summary(goal, None)
        assert result is not None
        assert "减重 5kg" in result
        assert "阶段" not in result

    def test_chapter_only(self) -> None:
        chapter = json.dumps({"title": "冲刺期", "milestone": "", "process_goals": []})
        result = extract_goal_chapter_summary(None, chapter)
        assert result is not None
        assert "冲刺期" in result
        assert "目标" not in result

    def test_process_goals_capped_at_three(self) -> None:
        chapter = json.dumps({
            "title": "测试",
            "milestone": "",
            "process_goals": [
                {"description": f"目标{i}", "target": f"{i}次"} for i in range(5)
            ],
        })
        result = extract_goal_chapter_summary(None, chapter)
        assert result is not None
        # 最多只展示前 3 个
        assert "目标3" not in result
        assert "目标4" not in result


class TestFormatBriefingWithGoalChapter:
    def test_goal_chapter_section_appears_before_briefing(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = format_briefing(
            days_since_last=1,
            sessions_this_week=3,
            upcoming_markers=[],
            lifesign_activity=[],
            goal_chapter_summary="目标：减重 10kg（2026-09-01）\n阶段：建立基础",
            now=now,
        )
        goal_pos = result.index("当前阶段")
        briefing_pos = result.index("Coach Briefing")
        assert goal_pos < briefing_pos

    def test_no_goal_chapter_omits_section(self) -> None:
        now = datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc)
        result = format_briefing(
            days_since_last=None,
            sessions_this_week=0,
            upcoming_markers=[],
            lifesign_activity=[],
            now=now,
        )
        assert "当前阶段" not in result


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
