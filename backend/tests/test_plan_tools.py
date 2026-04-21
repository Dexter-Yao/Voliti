# ABOUTME: Plan Skill 工具层单元测试
# ABOUTME: 覆盖 3 个 tool merge 语义 + archive-first 写入 + 自愈读取 + 拒绝边界

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest
from langgraph.store.memory import InMemoryStore

from voliti.contracts.plan import PlanDocument, PlanPatch
from voliti.store_contract import (
    PLAN_CURRENT_KEY,
    make_file_value,
    make_plan_archive_namespace,
    make_user_namespace,
    unwrap_file_value,
)
from voliti.tools.plan_tools import (
    _execute_plan_tool,
    _merge_revise_plan,
    _merge_set_goal_status,
    _merge_update_week_narrative,
    read_current_plan_with_self_heal,
    revise_plan,
    set_goal_status,
    update_week_narrative,
)


TEST_USER_ID = "plan_test_001"
CONFIG = {"configurable": {"user_id": TEST_USER_ID}}
USER_NS = make_user_namespace(TEST_USER_ID)
ARCHIVE_NS = make_plan_archive_namespace(TEST_USER_ID)


# ── fixtures ─────────────────────────────────────────────────────────────


def _baseline_plan_dict() -> dict[str, Any]:
    return {
        "plan_id": "plan_a",
        "status": "active",
        "version": 1,
        "target_summary": "两个月减 10 斤",
        "overall_narrative": "两个月前体重回到一个我自己都不认识的数字。",
        "started_at": "2026-02-21T00:00:00+08:00",
        "planned_end_at": "2026-04-17T23:59:59+08:00",
        "created_at": "2026-02-21T09:15:00+08:00",
        "revised_at": "2026-02-21T09:15:00+08:00",
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
                "start_date": "2026-03-06",
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
        "current_week": None,
    }


@pytest.fixture
def fixed_now() -> datetime:
    return datetime(2026, 3, 15, 7, 32, 0, tzinfo=timezone.utc)


@pytest.fixture
def baseline_plan() -> PlanDocument:
    return PlanDocument.model_validate(_baseline_plan_dict())


@pytest.fixture
def store_with_plan(baseline_plan: PlanDocument) -> InMemoryStore:
    """InMemoryStore 预置 /plan/current.json = baseline_plan v1。"""
    store = InMemoryStore()
    store.put(
        USER_NS,
        PLAN_CURRENT_KEY,
        make_file_value(baseline_plan.model_dump_json()),
    )
    return store


@pytest.fixture
def empty_store() -> InMemoryStore:
    return InMemoryStore()


# ── merge helpers 单测 ───────────────────────────────────────────────────


class TestMergeSetGoalStatus:
    def test_inserts_new_goal_status(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        new_plan = _merge_set_goal_status(
            baseline_plan, goal_name="每周三次训练", days_met=3, days_expected=3, now=fixed_now
        )
        assert new_plan.current_week is not None
        assert len(new_plan.current_week.goals_status) == 1
        assert new_plan.current_week.goals_status[0].goal_name == "每周三次训练"
        assert new_plan.current_week.goals_status[0].days_met == 3
        assert new_plan.revised_at == fixed_now

    def test_upsert_same_goal_name(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        """GAP 16: 同 goal_name 应覆盖不 append。"""
        first = _merge_set_goal_status(
            baseline_plan, goal_name="每周三次训练", days_met=2, days_expected=3, now=fixed_now
        )
        second = _merge_set_goal_status(
            first, goal_name="每周三次训练", days_met=3, days_expected=3, now=fixed_now
        )
        assert second.current_week is not None
        assert len(second.current_week.goals_status) == 1
        assert second.current_week.goals_status[0].days_met == 3

    def test_auto_init_current_week_when_none(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        """GAP 5: current_week=None 时应自动初始化。"""
        assert baseline_plan.current_week is None
        new_plan = _merge_set_goal_status(
            baseline_plan, goal_name="每周三次训练", days_met=1, days_expected=3, now=fixed_now
        )
        assert new_plan.current_week is not None
        assert new_plan.current_week.source == "coach_inferred"

    def test_infers_days_expected_from_chapter(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        """days_expected=None 时应从 chapter 的 weekly_target_days 推断。"""
        new_plan = _merge_set_goal_status(
            baseline_plan,
            goal_name="每周三次训练",
            days_met=2,
            days_expected=None,
            now=fixed_now,
        )
        assert new_plan.current_week is not None
        assert new_plan.current_week.goals_status[0].days_expected == 3   # chapter 2 的 weekly_target_days

    def test_rejects_when_plan_missing(self, fixed_now: datetime) -> None:
        """GAP 15: Plan 不存在时状态性 tool 应拒绝。"""
        from voliti.tools.plan_tools import PlanToolRejected

        with pytest.raises(PlanToolRejected) as exc_info:
            _merge_set_goal_status(
                None, goal_name="foo", days_met=1, days_expected=1, now=fixed_now
            )
        assert "Plan 尚未创建" in exc_info.value.message


class TestMergeUpdateWeekNarrative:
    def test_updates_highlights(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        new_plan = _merge_update_week_narrative(
            baseline_plan, highlights="状态回暖", concerns=None, now=fixed_now
        )
        assert new_plan.current_week is not None
        assert new_plan.current_week.highlights == "状态回暖"
        assert new_plan.current_week.concerns is None

    def test_updates_concerns(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        new_plan = _merge_update_week_narrative(
            baseline_plan, highlights=None, concerns="周六深夜失守", now=fixed_now
        )
        assert new_plan.current_week is not None
        assert new_plan.current_week.concerns == "周六深夜失守"

    def test_rejects_both_none(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        from voliti.tools.plan_tools import PlanToolRejected

        with pytest.raises(PlanToolRejected):
            _merge_update_week_narrative(
                baseline_plan, highlights=None, concerns=None, now=fixed_now
            )

    def test_rejects_when_plan_missing(self, fixed_now: datetime) -> None:
        from voliti.tools.plan_tools import PlanToolRejected

        with pytest.raises(PlanToolRejected):
            _merge_update_week_narrative(
                None, highlights="x", concerns=None, now=fixed_now
            )


class TestMergeRevisePlan:
    def test_rejects_empty_patch(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        """GAP 10: 空 patch 拒绝。"""
        from voliti.tools.plan_tools import PlanToolRejected

        with pytest.raises(PlanToolRejected) as exc_info:
            _merge_revise_plan(
                baseline_plan, patch=PlanPatch(), now=fixed_now
            )
        assert "不能为空" in exc_info.value.message

    def test_rejects_change_summary_only(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        """GAP 18: 仅 change_summary 无实质变化，拒绝。"""
        from voliti.tools.plan_tools import PlanToolRejected

        with pytest.raises(PlanToolRejected) as exc_info:
            _merge_revise_plan(
                baseline_plan,
                patch=PlanPatch(change_summary="只写说明"),
                now=fixed_now,
            )
        assert "change_summary" in exc_info.value.message

    def test_structural_patch_increments_version(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        """结构性 patch 应 version++。"""
        new_target = baseline_plan.target.model_copy(update={"rate_kg_per_week": 0.5})
        patch = PlanPatch(target=new_target, change_summary="降低周速度")
        new_plan = _merge_revise_plan(baseline_plan, patch=patch, now=fixed_now)
        assert new_plan.version == 2
        assert new_plan.predecessor_version == 1
        assert new_plan.target.rate_kg_per_week == 0.5

    def test_nonstructural_patch_keeps_version(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        """仅叙事字段变化不归档，version 不变。"""
        patch = PlanPatch(overall_narrative="新的叙事文本，至少十个字符用于通过 min_length 约束。")
        new_plan = _merge_revise_plan(baseline_plan, patch=patch, now=fixed_now)
        assert new_plan.version == 1
        assert new_plan.predecessor_version is None

    def test_chapter_patch_locates_by_chapter_index(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        """GAP 17: ChapterPatch 按 chapter_index 定位合并，其他 chapter 保留。"""
        from voliti.contracts.plan import ChapterPatch

        patch = PlanPatch(
            chapters=[ChapterPatch(chapter_index=2, milestone="新的里程碑描述")],
        )
        new_plan = _merge_revise_plan(baseline_plan, patch=patch, now=fixed_now)
        assert new_plan.chapters[0].milestone == baseline_plan.chapters[0].milestone
        assert new_plan.chapters[1].milestone == "新的里程碑描述"
        # 未 patch 的字段保留
        assert new_plan.chapters[1].weekly_training_count == 3

    def test_chapter_patch_unknown_index_rejected(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        from voliti.contracts.plan import ChapterPatch
        from voliti.tools.plan_tools import PlanToolRejected

        patch = PlanPatch(
            chapters=[ChapterPatch(chapter_index=5, milestone="不存在的 chapter")],
        )
        with pytest.raises(PlanToolRejected) as exc_info:
            _merge_revise_plan(baseline_plan, patch=patch, now=fixed_now)
        assert "chapter_index=5" in exc_info.value.message

    def test_rejects_when_plan_missing(self, fixed_now: datetime) -> None:
        from voliti.tools.plan_tools import PlanToolRejected

        patch = PlanPatch(change_summary="首次创建", overall_narrative="十个字符以上叙事文本。")
        with pytest.raises(PlanToolRejected):
            _merge_revise_plan(None, patch=patch, now=fixed_now)


# ── archive-first 写入 + 自愈读取 ─────────────────────────────────────────


class TestArchiveFirstAndSelfHeal:
    def test_revise_plan_structural_writes_archive_and_current(
        self,
        store_with_plan: InMemoryStore,
        baseline_plan: PlanDocument,
    ) -> None:
        """结构性 revise → archive v2 文件存在 + current 更新到 v2。"""
        new_target = baseline_plan.target.model_copy(update={"rate_kg_per_week": 0.5})
        patch_dict = {
            "target": new_target.model_dump(),
            "change_summary": "降低周速度",
        }
        # 直接调 .func 绕过 InjectedToolArg
        result = revise_plan.func(
            patch=patch_dict,
            store=store_with_plan,
            config=CONFIG,
        )
        assert "已归档" in result
        assert "v2" in result

        # archive 有 v2 文件
        items = store_with_plan.search(ARCHIVE_NS, limit=10)
        keys = [it.key for it in items]
        assert any("plan_a_v2.json" in k for k in keys)

        # current 版本更新为 v2
        current_item = store_with_plan.get(USER_NS, PLAN_CURRENT_KEY)
        assert current_item is not None
        doc = PlanDocument.model_validate_json(unwrap_file_value(current_item.value))
        assert doc.version == 2

    def test_set_goal_status_no_archive(
        self,
        store_with_plan: InMemoryStore,
    ) -> None:
        """状态性 tool 不产生 archive。"""
        result = set_goal_status.func(
            goal_name="每周三次训练",
            days_met=2,
            days_expected=3,
            store=store_with_plan,
            config=CONFIG,
        )
        assert "version 保持 1" in result
        archive_items = store_with_plan.search(ARCHIVE_NS, limit=10)
        assert len(archive_items) == 0

    def test_self_heal_rewrites_current_from_archive(
        self, baseline_plan: PlanDocument
    ) -> None:
        """GAP 24 critical test: archive v3 存在 + current v2 → 下次读触发自愈重写 current 为 v3。"""
        store = InMemoryStore()

        # 构造 current v2
        v2 = baseline_plan.model_copy(update={"version": 2, "predecessor_version": 1})
        store.put(USER_NS, PLAN_CURRENT_KEY, make_file_value(v2.model_dump_json()))

        # 构造 archive 中 v3（比 current 新）
        v3 = baseline_plan.model_copy(
            update={"version": 3, "predecessor_version": 2, "change_summary": "修订"}
        )
        store.put(
            ARCHIVE_NS,
            "plan_a_v3.json",
            make_file_value(v3.model_dump_json()),
        )

        result = read_current_plan_with_self_heal(store, USER_NS, ARCHIVE_NS)
        assert result is not None
        assert result.version == 3

        # 自愈后 current 被重写为 v3
        current_item = store.get(USER_NS, PLAN_CURRENT_KEY)
        assert current_item is not None
        healed = PlanDocument.model_validate_json(unwrap_file_value(current_item.value))
        assert healed.version == 3

    def test_self_heal_handles_corrupt_current(
        self, baseline_plan: PlanDocument
    ) -> None:
        """current 损坏但 archive 有 v1 → 自愈读出 v1。"""
        store = InMemoryStore()
        store.put(
            USER_NS,
            PLAN_CURRENT_KEY,
            make_file_value("not valid json at all {{{{"),
        )
        store.put(
            ARCHIVE_NS,
            "plan_a_v1.json",
            make_file_value(baseline_plan.model_dump_json()),
        )

        result = read_current_plan_with_self_heal(store, USER_NS, ARCHIVE_NS)
        assert result is not None
        assert result.version == 1

    def test_self_heal_returns_none_for_new_user(self) -> None:
        """无 current 无 archive → 返回 None（新用户场景）。"""
        store = InMemoryStore()
        result = read_current_plan_with_self_heal(store, USER_NS, ARCHIVE_NS)
        assert result is None

    def test_self_heal_archive_corrupt_skipped(
        self, baseline_plan: PlanDocument
    ) -> None:
        """某 archive 文件损坏 → 跳过，使用下一个合法的。"""
        store = InMemoryStore()
        v1 = baseline_plan
        store.put(USER_NS, PLAN_CURRENT_KEY, make_file_value(v1.model_dump_json()))
        # archive v2 损坏
        store.put(
            ARCHIVE_NS,
            "plan_a_v2.json",
            make_file_value("garbage"),
        )
        # 此时 archive 最大合法版本为空，current=v1，函数应返回 v1 不崩
        result = read_current_plan_with_self_heal(store, USER_NS, ARCHIVE_NS)
        assert result is not None
        assert result.version == 1


# ── tool happy path 端到端 ───────────────────────────────────────────────


class TestToolEndToEnd:
    def test_set_goal_status_happy_path(
        self, store_with_plan: InMemoryStore
    ) -> None:
        result = set_goal_status.func(
            goal_name="每周三次训练",
            days_met=2,
            days_expected=3,
            store=store_with_plan,
            config=CONFIG,
        )
        assert "写入成功" in result

        current_item = store_with_plan.get(USER_NS, PLAN_CURRENT_KEY)
        doc = PlanDocument.model_validate_json(unwrap_file_value(current_item.value))
        assert doc.current_week is not None
        assert doc.current_week.goals_status[0].goal_name == "每周三次训练"

    def test_set_goal_status_unknown_goal_rejected(
        self, store_with_plan: InMemoryStore
    ) -> None:
        """GAP 3: 未知 goal_name → Pydantic @model_validator #4 拒绝 + actionable 错误。"""
        result = set_goal_status.func(
            goal_name="晨间冥想",   # 不在任何 chapter 的 process_goals 中
            days_met=3,
            days_expected=5,
            store=store_with_plan,
            config=CONFIG,
        )
        assert "goal_name" in result
        assert "晨间冥想" in result
        assert "可用 goal_name" in result

    def test_set_goal_status_plan_missing_rejected(
        self, empty_store: InMemoryStore
    ) -> None:
        result = set_goal_status.func(
            goal_name="x",
            days_met=1,
            days_expected=1,
            store=empty_store,
            config=CONFIG,
        )
        assert "Plan 尚未创建" in result

    def test_update_week_narrative_both_none_rejected(
        self, store_with_plan: InMemoryStore
    ) -> None:
        result = update_week_narrative.func(
            highlights=None,
            concerns=None,
            store=store_with_plan,
            config=CONFIG,
        )
        assert "至少需要" in result

    def test_revise_plan_empty_patch_rejected(
        self, store_with_plan: InMemoryStore
    ) -> None:
        result = revise_plan.func(
            patch={},
            store=store_with_plan,
            config=CONFIG,
        )
        assert "不能为空" in result

    def test_revise_plan_change_summary_only_rejected(
        self, store_with_plan: InMemoryStore
    ) -> None:
        result = revise_plan.func(
            patch={"change_summary": "无实质修改"},
            store=store_with_plan,
            config=CONFIG,
        )
        assert "change_summary" in result

    def test_revise_plan_validation_error_fail_closed(
        self, store_with_plan: InMemoryStore
    ) -> None:
        """patch 含非法字段值 → PlanPatch 层先拒，actionable 错误。"""
        result = revise_plan.func(
            patch={"target": {"metric": "weight_kg", "baseline": 70.0,
                              "goal_value": 65.0, "duration_weeks": 8,
                              "rate_kg_per_week": 2.5}},   # 超健康阈值
            store=store_with_plan,
            config=CONFIG,
        )
        # 错误消息应包含字段路径
        assert "rate_kg_per_week" in result
