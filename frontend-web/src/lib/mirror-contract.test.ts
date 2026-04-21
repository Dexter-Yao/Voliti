// ABOUTME: Mirror Plan 适配层测试
// ABOUTME: 验证 buildMirrorDataFromPlan 把 PlanDocument + PlanViewRecord 投影为 Mirror 所需视图

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import {
  buildAcceptedWitnessCardsFromStoreItems,
  buildMirrorDataFromPlan,
  type PlanDocumentData,
  type PlanViewData,
} from "./mirror-contract";

function loadFixture(name: string): Record<string, unknown> {
  const path = resolve(process.cwd(), "../tests/contracts/fixtures/store", name);
  return JSON.parse(readFileSync(path, "utf-8")) as Record<string, unknown>;
}

function buildPlanFixture(): PlanDocumentData {
  return {
    plan_id: "plan_fixture_001",
    status: "active",
    version: 1,
    predecessor_version: null,
    supersedes_plan_id: null,
    change_summary: null,
    target_summary: "12 周内从 75kg 减至 70kg",
    overall_narrative: "通过建立饮食节奏与力量训练两阶段实现减脂。",
    started_at: "2026-04-01T00:00:00+08:00",
    planned_end_at: "2026-06-24T00:00:00+08:00",
    created_at: "2026-04-01T00:00:00+08:00",
    revised_at: "2026-04-19T10:00:00+08:00",
    target: {
      metric: "weight_kg",
      baseline: 75,
      goal_value: 70,
      duration_weeks: 12,
      rate_kg_per_week: 0.5,
    },
    chapters: [
      {
        chapter_index: 1,
        name: "建立饮食节奏",
        why_this_chapter: "先把饮食稳住",
        previous_chapter_id: null,
        revision_of: null,
        start_date: "2026-04-01",
        end_date: "2026-04-29",
        milestone: "蛋白质达标率 ≥ 70%",
        process_goals: [
          {
            name: "饮食记录",
            why_this_goal: null,
            weekly_target_days: 5,
            weekly_total_days: 7,
            how_to_measure: "在 app 中记录三餐",
            examples: [],
          },
        ],
        daily_rhythm: {
          meals: { value: "三餐主食减半", tooltip: "午餐鸡胸糙米" },
          training: { value: "每周 3 次快走", tooltip: "每次 30 分钟" },
          sleep: { value: "23:30 前入睡", tooltip: "睡前不进食" },
        },
        daily_calorie_range: [1400, 1700],
        daily_protein_grams_range: [90, 120],
        weekly_training_count: 3,
      },
    ],
    linked_lifesigns: [],
    linked_markers: [],
    current_week: null,
  };
}

function buildPlanViewFixture(): PlanViewData {
  return {
    plan_phase: "in_chapter",
    active_chapter_index: 1,
    week_index: 3,
    day_progress: [20, 84],
    days_left_in_chapter: 9,
    map_state: {
      flag_ratio: 0.24,
      events: [],
    },
    week_view: [],
    week_freshness: null,
    day_template: [
      { label: "meals", value: "三餐主食减半", tooltip: "午餐鸡胸糙米" },
      { label: "training", value: "每周 3 次快走", tooltip: "每次 30 分钟" },
      { label: "sleep", value: "23:30 前入睡", tooltip: "睡前不进食" },
    ],
    watch_list: [],
  };
}

describe("buildMirrorDataFromPlan", () => {
  it("projects active chapter fields from plan + plan_view", () => {
    const data = buildMirrorDataFromPlan({
      plan: buildPlanFixture(),
      planView: buildPlanViewFixture(),
      dashboardConfigValue: loadFixture("dashboard_config.value.json"),
      profileValue: loadFixture("profile_context.value.json"),
    });

    expect(data.chapter?.title).toBe("建立饮食节奏");
    expect(data.chapter?.chapter_number).toBe(1);
    expect(data.chapter?.process_goals[0]?.description).toBe("饮食记录");
    expect(data.chapter?.process_goals[0]?.target).toBe("5/7");
    expect(data.goal?.description).toBe("12 周内从 75kg 减至 70kg");
    expect(data.goal?.north_star_target.unit).toBe("kg");
    expect(data.identity_statement).toContain("清醒选择");
    expect(data.dashboardConfig?.north_star.label).toBe("体重趋势");
  });

  it("returns null chapter when plan_view has no active chapter", () => {
    const planView = buildPlanViewFixture();
    planView.active_chapter_index = null;
    planView.plan_phase = "before_start";

    const data = buildMirrorDataFromPlan({
      plan: buildPlanFixture(),
      planView,
    });

    expect(data.chapter).toBeNull();
    expect(data.goal?.description).toBe("12 周内从 75kg 减至 70kg");
  });
});

describe("buildAcceptedWitnessCardsFromStoreItems", () => {
  it("keeps only accepted witness cards and orders them by newest first", () => {
    const cards = buildAcceptedWitnessCardsFromStoreItems([
      {
        key: "card_pending",
        value: {
          achievement_title: "尚未收下",
          imageData: "data:image/jpeg;base64,pending",
          narrative: "pending",
          status: "pending",
          timestamp: "2026-04-18T01:00:00Z",
        },
      },
      {
        key: "card_old",
        value: {
          achievement_title: "较早收下",
          imageData: "data:image/jpeg;base64,old",
          narrative: "old",
          status: "accepted",
          timestamp: "2026-04-18T02:00:00Z",
        },
      },
      {
        key: "card_new",
        value: {
          achievement_title: "最新收下",
          imageData: "data:image/jpeg;base64,new",
          narrative: "new",
          status: "accepted",
          timestamp: "2026-04-18T03:00:00Z",
        },
      },
    ]);

    expect(cards).toEqual([
      {
        achievementType: "explicit",
        id: "card_new",
        narrative: "new",
        src: "data:image/jpeg;base64,new",
        alt: "最新收下",
        createdAt: "2026-04-18T03:00:00Z",
      },
      {
        achievementType: "explicit",
        id: "card_old",
        narrative: "old",
        src: "data:image/jpeg;base64,old",
        alt: "较早收下",
        createdAt: "2026-04-18T02:00:00Z",
      },
    ]);
  });
});
