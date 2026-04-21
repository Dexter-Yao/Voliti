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
    _apply_plan_builder_submission,
    _build_plan_builder_components,
    _execute_plan_tool,
    _merge_create_plan,
    _merge_revise_plan,
    _merge_set_goal_status,
    _merge_update_week_narrative,
    create_plan,
    fan_out_plan_builder,
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


# ── create_plan 首次创建 ───────────────────────────────────────────────────


class TestMergeCreatePlan:
    def test_rejects_when_plan_already_exists(
        self, baseline_plan: PlanDocument, fixed_now: datetime
    ) -> None:
        with pytest.raises(Exception) as exc_info:
            _merge_create_plan(
                baseline_plan,
                document=_baseline_plan_dict(),
                now=fixed_now,
            )
        assert "Plan 已存在" in str(exc_info.value)

    def test_creates_when_no_current_plan(self, fixed_now: datetime) -> None:
        document = _baseline_plan_dict()
        plan = _merge_create_plan(None, document=document, now=fixed_now)
        assert plan.version == 1
        assert plan.predecessor_version is None
        assert plan.status == "active"
        assert plan.created_at == fixed_now
        assert plan.revised_at == fixed_now

    def test_overrides_coach_supplied_version(self, fixed_now: datetime) -> None:
        """即使 Coach 传入 version=5，系统也强制 version=1。"""
        document = _baseline_plan_dict() | {"version": 5, "predecessor_version": 4}
        plan = _merge_create_plan(None, document=document, now=fixed_now)
        assert plan.version == 1
        assert plan.predecessor_version is None

    def test_validation_error_surfaces_as_rejection(
        self, fixed_now: datetime
    ) -> None:
        from voliti.tools.plan_tools import PlanToolRejected

        bad_doc = _baseline_plan_dict()
        # 让第二章 start_date 不等于第一章 end_date，触发 chapter timeline 校验
        bad_doc["chapters"][1]["start_date"] = "2026-03-10"
        with pytest.raises(PlanToolRejected) as exc_info:
            _merge_create_plan(None, document=bad_doc, now=fixed_now)
        assert "Chapter 1" in exc_info.value.message
        assert "不连续" in exc_info.value.message


class TestCreatePlanEndToEnd:
    def test_create_plan_happy_path(self, empty_store: InMemoryStore) -> None:
        """新用户场景：current 与 archive 皆空，create_plan 应 archive-first 写 v1。"""
        document = _baseline_plan_dict()
        result = create_plan.func(
            document=document, store=empty_store, config=CONFIG
        )
        assert "写入成功" in result
        assert "version 1" in result

        current_item = empty_store.get(USER_NS, PLAN_CURRENT_KEY)
        assert current_item is not None
        doc = PlanDocument.model_validate_json(unwrap_file_value(current_item.value))
        assert doc.plan_id == "plan_a"
        assert doc.version == 1

        archive_items = list(empty_store.search(ARCHIVE_NS, limit=10))
        assert len(archive_items) == 1
        assert archive_items[0].key == "plan_a_v1.json"

    def test_create_plan_rejects_when_plan_exists(
        self, store_with_plan: InMemoryStore
    ) -> None:
        document = _baseline_plan_dict()
        result = create_plan.func(
            document=document, store=store_with_plan, config=CONFIG
        )
        assert "Plan 已存在" in result

    def test_create_plan_validation_error_fail_closed(
        self, empty_store: InMemoryStore
    ) -> None:
        bad_doc = _baseline_plan_dict()
        bad_doc["target"]["rate_kg_per_week"] = 2.5   # 超健康阈值
        result = create_plan.func(
            document=bad_doc, store=empty_store, config=CONFIG
        )
        assert "rate_kg_per_week" in result
        # 失败时 current 与 archive 都不应被写入
        assert empty_store.get(USER_NS, PLAN_CURRENT_KEY) is None
        assert list(empty_store.search(ARCHIVE_NS, limit=10)) == []


# ── Plan Builder（C.3.a）───────────────────────────────────────────────────


class TestBuildPlanBuilderComponents:
    def test_returns_none_for_unknown_chapter_index(
        self, baseline_plan: PlanDocument
    ) -> None:
        assert _build_plan_builder_components(baseline_plan, 99) is None

    def test_emits_four_text_inputs_with_stable_keys(
        self, baseline_plan: PlanDocument
    ) -> None:
        components = _build_plan_builder_components(baseline_plan, 1)
        assert components is not None
        input_keys = [c["key"] for c in components if c["kind"] == "text_input"]
        assert input_keys == [
            "milestone",
            "rhythm.meals",
            "rhythm.training",
            "rhythm.sleep",
        ]

    def test_numeric_fields_go_into_a_text_only_row(
        self, baseline_plan: PlanDocument
    ) -> None:
        """热量 / 蛋白 / 训练次数 C.3.a 只读，以 text 合并呈现。"""
        components = _build_plan_builder_components(baseline_plan, 1)
        assert components is not None
        numeric_rows = [
            c for c in components if c["kind"] == "text" and "kcal" in c.get("text", "")
        ]
        assert len(numeric_rows) == 1
        assert "蛋白" in numeric_rows[0]["text"]
        assert "每周训练" in numeric_rows[0]["text"]

    def test_top_of_panel_anchors_user_narrative(
        self, baseline_plan: PlanDocument
    ) -> None:
        """第一条组件应呈现用户自己的 overall_narrative，让共建感以"被看见"开场。"""
        components = _build_plan_builder_components(baseline_plan, 1)
        assert components is not None
        assert components[0]["kind"] == "text"
        assert baseline_plan.overall_narrative in components[0]["text"]


class TestApplyPlanBuilderSubmission:
    def test_empty_submission_yields_no_patch(
        self, baseline_plan: PlanDocument
    ) -> None:
        patch, changes = _apply_plan_builder_submission(baseline_plan, 1, {})
        assert patch == {}
        assert changes == []

    def test_unchanged_values_are_filtered_out(
        self, baseline_plan: PlanDocument
    ) -> None:
        data = {
            "milestone": baseline_plan.chapters[0].milestone,
            "rhythm.meals": baseline_plan.chapters[0].daily_rhythm.meals.value,
        }
        patch, changes = _apply_plan_builder_submission(baseline_plan, 1, data)
        assert patch == {}
        assert changes == []

    def test_milestone_change_produces_chapter_patch(
        self, baseline_plan: PlanDocument
    ) -> None:
        data = {"milestone": "连续三周早餐蛋白 5/7"}
        patch, changes = _apply_plan_builder_submission(baseline_plan, 1, data)
        assert patch["chapters"][0]["chapter_index"] == 1
        assert patch["chapters"][0]["milestone"] == "连续三周早餐蛋白 5/7"
        assert changes == ["本章目标 → 连续三周早餐蛋白 5/7"]

    def test_rhythm_change_includes_full_rhythm_and_keeps_existing_tooltips(
        self, baseline_plan: PlanDocument
    ) -> None:
        """daily_rhythm 是嵌套 model，patch 需整体给出；未改动 slot 的 tooltip 必须保留。"""
        data = {"rhythm.training": "每周三次 · 力量为主"}
        patch, changes = _apply_plan_builder_submission(baseline_plan, 1, data)
        chapter_patch = patch["chapters"][0]
        assert chapter_patch["daily_rhythm"]["training"]["value"] == "每周三次 · 力量为主"
        # meals / sleep 沿用原 value + tooltip
        assert chapter_patch["daily_rhythm"]["meals"]["value"] == baseline_plan.chapters[0].daily_rhythm.meals.value
        assert chapter_patch["daily_rhythm"]["meals"]["tooltip"] == baseline_plan.chapters[0].daily_rhythm.meals.tooltip
        assert changes == ["训练 → 每周三次 · 力量为主"]

    def test_unknown_keys_are_ignored(self, baseline_plan: PlanDocument) -> None:
        """C.3.b.1 后：未知 key（协议演进后残留字段 / Coach 传错 key）不破坏整体翻译。"""
        data = {"legacy_foo": "9", "something_else": "x", "milestone": "新目标"}
        patch, changes = _apply_plan_builder_submission(baseline_plan, 1, data)
        assert "chapters" in patch
        # 未知 key 不进入 patch
        assert patch["chapters"][0].get("legacy_foo") is None
        assert patch["chapters"][0].get("something_else") is None
        assert changes == ["本章目标 → 新目标"]

    def test_empty_whitespace_values_are_ignored(
        self, baseline_plan: PlanDocument
    ) -> None:
        data = {"milestone": "   ", "rhythm.meals": ""}
        patch, changes = _apply_plan_builder_submission(baseline_plan, 1, data)
        assert patch == {}
        assert changes == []


class TestFanOutPlanBuilderGuards:
    def test_rejects_when_plan_missing(self, empty_store: InMemoryStore) -> None:
        result = fan_out_plan_builder.func(
            chapter_index=None, store=empty_store, config=CONFIG
        )
        assert "Plan 尚未创建" in result

    def test_rejects_unknown_chapter_index(
        self, store_with_plan: InMemoryStore
    ) -> None:
        result = fan_out_plan_builder.func(
            chapter_index=99, store=store_with_plan, config=CONFIG
        )
        assert "不对应任何已有 chapter" in result
        assert "可用 chapter_index" in result


# ── Plan Builder 数值字段（C.3.b.1）────────────────────────────────────────


class TestEditableFieldToSlider:
    def test_rejects_non_slider_kind(
        self, baseline_plan: PlanDocument
    ) -> None:
        from voliti.tools.plan_tools import _editable_field_to_slider

        spec = {"key": "weekly_training_count", "kind": "text_input", "min": 2, "max": 4, "label": "x"}
        assert _editable_field_to_slider(spec, baseline_plan.chapters[0]) is None

    def test_rejects_min_greater_than_max(
        self, baseline_plan: PlanDocument
    ) -> None:
        from voliti.tools.plan_tools import _editable_field_to_slider

        spec = {"key": "weekly_training_count", "kind": "slider", "min": 5, "max": 3, "label": "x"}
        assert _editable_field_to_slider(spec, baseline_plan.chapters[0]) is None

    def test_rejects_unknown_key(
        self, baseline_plan: PlanDocument
    ) -> None:
        from voliti.tools.plan_tools import _editable_field_to_slider

        spec = {"key": "blood_pressure", "kind": "slider", "min": 0, "max": 100, "label": "x"}
        assert _editable_field_to_slider(spec, baseline_plan.chapters[0]) is None

    def test_clamps_initial_value_into_coach_range(
        self, baseline_plan: PlanDocument
    ) -> None:
        """当前 chapter 的 weekly_training_count=2，Coach 给 [3, 5]，slider 初值应 clamp 到 3。"""
        from voliti.tools.plan_tools import _editable_field_to_slider

        spec = {"key": "weekly_training_count", "kind": "slider",
                "min": 3, "max": 5, "step": 1, "label": "每周训练次数"}
        slider = _editable_field_to_slider(spec, baseline_plan.chapters[0])
        assert slider == {
            "kind": "slider",
            "key": "weekly_training_count",
            "label": "每周训练次数",
            "min": 3,
            "max": 5,
            "step": 1,
            "value": 3,
        }

    def test_resolves_process_goal_index_path(
        self, baseline_plan: PlanDocument
    ) -> None:
        from voliti.tools.plan_tools import _editable_field_to_slider

        spec = {
            "key": "process_goals.0.weekly_target_days",
            "kind": "slider",
            "min": 3,
            "max": 7,
            "label": "早餐蛋白目标天数",
        }
        slider = _editable_field_to_slider(spec, baseline_plan.chapters[0])
        assert slider is not None
        # chapter 1 的 process_goals[0].weekly_target_days == 5
        assert slider["value"] == 5


class TestBuildPlanBuilderComponentsWithEditableFields:
    def test_without_editable_fields_preserves_readonly_summary(
        self, baseline_plan: PlanDocument
    ) -> None:
        """不传 editable_fields 时，保持 C.3.a 的只读聚合行。"""
        components = _build_plan_builder_components(baseline_plan, 1, None)
        assert components is not None
        readonly_rows = [
            c for c in components if c["kind"] == "text" and "kcal" in c.get("text", "")
        ]
        assert len(readonly_rows) == 1
        assert "蛋白" in readonly_rows[0]["text"] and "每周训练" in readonly_rows[0]["text"]

    def test_editable_field_emits_hint_before_slider(
        self, baseline_plan: PlanDocument
    ) -> None:
        editable = [
            {
                "key": "weekly_training_count",
                "kind": "slider",
                "min": 2,
                "max": 3,
                "label": "每周训练次数",
                "hint": "新手阶段 2-3 次稳定比 4 次断续更值",
            }
        ]
        components = _build_plan_builder_components(baseline_plan, 1, editable)
        assert components is not None
        kinds = [c["kind"] for c in components]
        # 期望末尾出现 text("数值调整") -> text(hint) -> slider
        slider_pos = next(i for i, c in enumerate(components) if c["kind"] == "slider")
        assert components[slider_pos - 1]["text"] == "新手阶段 2-3 次稳定比 4 次断续更值"
        assert components[slider_pos - 2]["text"] == "数值调整"
        assert "slider" in kinds

    def test_readonly_summary_drops_edited_fields(
        self, baseline_plan: PlanDocument
    ) -> None:
        """weekly_training_count 被开放编辑 → 只读聚合行不再重复列出它。"""
        editable = [
            {"key": "weekly_training_count", "kind": "slider",
             "min": 2, "max": 3, "label": "每周训练次数"}
        ]
        components = _build_plan_builder_components(baseline_plan, 1, editable)
        assert components is not None
        readonly_rows = [
            c for c in components
            if c["kind"] == "text"
            and ("kcal" in c.get("text", "") or "每周训练" in c.get("text", ""))
            and "数值调整" not in c.get("text", "")
        ]
        # 热量 + 蛋白仍在只读行；每周训练不再出现
        assert len(readonly_rows) == 1
        assert "每周训练" not in readonly_rows[0]["text"]
        assert "热量" in readonly_rows[0]["text"]
        assert "蛋白" in readonly_rows[0]["text"]

    def test_invalid_spec_is_silently_skipped(
        self, baseline_plan: PlanDocument
    ) -> None:
        """Coach 传错一个 spec 不应让整个 panel 失败。"""
        editable = [
            {"key": "made_up_field", "kind": "slider", "min": 0, "max": 100, "label": "x"},
            {"key": "weekly_training_count", "kind": "slider",
             "min": 2, "max": 3, "label": "每周训练次数"},
        ]
        components = _build_plan_builder_components(baseline_plan, 1, editable)
        assert components is not None
        sliders = [c for c in components if c["kind"] == "slider"]
        assert len(sliders) == 1
        assert sliders[0]["key"] == "weekly_training_count"


class TestApplyPlanBuilderSubmissionNumericFields:
    def test_weekly_training_count_integer(
        self, baseline_plan: PlanDocument
    ) -> None:
        # chapter 1 的 weekly_training_count=2
        patch, changes = _apply_plan_builder_submission(
            baseline_plan, 1, {"weekly_training_count": 3}
        )
        assert patch["chapters"][0]["weekly_training_count"] == 3
        assert "每周训练次数 → 3" in changes

    def test_weekly_training_count_accepts_string_digits(
        self, baseline_plan: PlanDocument
    ) -> None:
        """A2UI slider 可能把 int 序列化为 str（取决于前端传递），兼容两种。"""
        patch, _ = _apply_plan_builder_submission(
            baseline_plan, 1, {"weekly_training_count": "3"}
        )
        assert patch["chapters"][0]["weekly_training_count"] == 3

    def test_range_lower_only_preserves_upper(
        self, baseline_plan: PlanDocument
    ) -> None:
        """只改 calorie 下限时，上限必须保留原值。"""
        patch, changes = _apply_plan_builder_submission(
            baseline_plan, 1, {"daily_calorie_range.lower": 1600}
        )
        assert patch["chapters"][0]["daily_calorie_range"] == [1600, 1800]
        assert any("热量区间 → 1600-1800" in c for c in changes)

    def test_range_both_endpoints_changed(
        self, baseline_plan: PlanDocument
    ) -> None:
        patch, _ = _apply_plan_builder_submission(
            baseline_plan,
            1,
            {"daily_calorie_range.lower": 1550, "daily_calorie_range.upper": 1750},
        )
        assert patch["chapters"][0]["daily_calorie_range"] == [1550, 1750]

    def test_range_lower_greater_than_upper_is_ignored(
        self, baseline_plan: PlanDocument
    ) -> None:
        """用户把 lower 拉过 upper（前端约束应防止，但防御性处理）→ 保持原值。"""
        patch, changes = _apply_plan_builder_submission(
            baseline_plan,
            1,
            {"daily_calorie_range.lower": 2000, "daily_calorie_range.upper": 1600},
        )
        assert "daily_calorie_range" not in patch.get("chapters", [{}])[0]
        assert not any("热量" in c for c in changes)

    def test_protein_range_change(self, baseline_plan: PlanDocument) -> None:
        patch, changes = _apply_plan_builder_submission(
            baseline_plan, 1, {"daily_protein_grams_range.upper": 125}
        )
        assert patch["chapters"][0]["daily_protein_grams_range"] == [90, 125]
        assert any("蛋白区间 → 90-125 g" in c for c in changes)

    def test_process_goal_weekly_target_days_rewrites_list(
        self, baseline_plan: PlanDocument
    ) -> None:
        patch, changes = _apply_plan_builder_submission(
            baseline_plan, 1, {"process_goals.0.weekly_target_days": 6}
        )
        pgs = patch["chapters"][0]["process_goals"]
        # chapter 1 只有一个 process_goal；应整体重写且新值生效
        assert len(pgs) == 1
        assert pgs[0]["weekly_target_days"] == 6
        assert pgs[0]["name"] == "早餐蛋白 25 克以上"
        assert any("早餐蛋白 25 克以上 目标 → 6/周" in c for c in changes)

    def test_process_goal_out_of_range_index_ignored(
        self, baseline_plan: PlanDocument
    ) -> None:
        patch, changes = _apply_plan_builder_submission(
            baseline_plan, 1, {"process_goals.7.weekly_target_days": 6}
        )
        assert patch == {}
        assert changes == []

    def test_numeric_no_change_produces_no_patch(
        self, baseline_plan: PlanDocument
    ) -> None:
        data = {
            "weekly_training_count": 2,  # 与 chapter 1 当前值相同
            "daily_calorie_range.lower": 1500,
            "daily_calorie_range.upper": 1800,
        }
        patch, changes = _apply_plan_builder_submission(baseline_plan, 1, data)
        assert patch == {}
        assert changes == []

    def test_mixed_text_and_numeric_changes_stack_in_one_patch(
        self, baseline_plan: PlanDocument
    ) -> None:
        data = {
            "milestone": "连续三周早餐蛋白 5/7",
            "rhythm.training": "每周三次",
            "weekly_training_count": 3,
        }
        patch, changes = _apply_plan_builder_submission(baseline_plan, 1, data)
        chapter_patch = patch["chapters"][0]
        assert chapter_patch["milestone"] == "连续三周早餐蛋白 5/7"
        assert chapter_patch["weekly_training_count"] == 3
        assert chapter_patch["daily_rhythm"]["training"]["value"] == "每周三次"
        # 三条变更都应出现在摘要里
        assert len(changes) == 3
