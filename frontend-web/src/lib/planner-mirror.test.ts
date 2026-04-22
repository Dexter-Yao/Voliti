// ABOUTME: Planner Mirror 投影纯函数测试
// ABOUTME: 锁定 active-plan 区块只消费 plan 与 planView，不再依赖 raw store 派生

import { describe, expect, it } from "vitest";

import type { PlanDocumentData, PlanViewData } from "./mirror-contract";
import {
  buildPlannerEventStream,
  buildPlannerLifeSigns,
  buildPlannerProcessMetrics,
} from "./planner-mirror";

function buildPlan(): PlanDocumentData {
  return {
    plan_id: "plan_test",
    status: "active",
    version: 1,
    predecessor_version: null,
    supersedes_plan_id: null,
    change_summary: null,
    target_summary: "两个月减 10 斤",
    overall_narrative: "测试用 narrative",
    started_at: "2026-04-01T00:00:00+08:00",
    planned_end_at: "2026-06-01T00:00:00+08:00",
    created_at: "2026-04-01T00:00:00+08:00",
    revised_at: "2026-04-20T00:00:00+08:00",
    target: {
      metric: "weight_kg",
      baseline: 70,
      goal_value: 65,
      duration_weeks: 8,
      rate_kg_per_week: 0.625,
    },
    chapters: [
      {
        chapter_index: 1,
        name: "立起早餐",
        why_this_chapter: "先把早段节奏立起来。",
        previous_chapter_id: null,
        revision_of: null,
        start_date: "2026-04-01",
        end_date: "2026-04-21",
        milestone: "早餐蛋白 5/7",
        process_goals: [
          {
            name: "早餐蛋白 25 克以上",
            why_this_goal: "先稳住白天的饱腹感",
            weekly_target_days: 5,
            weekly_total_days: 7,
            how_to_measure: "记录早餐蛋白来源",
            examples: [],
          },
        ],
        daily_rhythm: {
          meals: { value: "三餐", tooltip: "稳定三餐" },
          training: { value: "每周两次", tooltip: "先求保底" },
          sleep: { value: "23:30 前", tooltip: "先稳作息" },
        },
        daily_calorie_range: [1500, 1800],
        daily_protein_grams_range: [90, 110],
        weekly_training_count: 2,
      },
    ],
    linked_lifesigns: [],
    linked_markers: [],
    current_week: null,
  };
}

function buildView(): PlanViewData {
  return {
    plan_phase: "in_chapter",
    active_chapter_index: 1,
    week_index: 3,
    day_progress: [14, 56],
    active_chapter_day_progress: [7, 21],
    days_left_in_chapter: 14,
    map_state: {
      flag_ratio: 0.25,
      events: [
        {
          id: "mk_trip",
          name: "出差",
          event_date: "2026-04-25",
          urgency: 0.8,
          description: "月底出差",
          is_past: false,
          risk_level: "high",
        },
      ],
    },
    week_view: [
      {
        goal_name: "早餐蛋白 25 克以上",
        days_met: 3,
        days_expected: 5,
      },
    ],
    week_freshness: null,
    day_template: [],
    watch_list: [
      {
        kind: "lifesign",
        id: "ls_night",
        name: "深夜加餐",
        event_date: null,
        risk_level: null,
        note: null,
        relevant_chapters: [1],
        trigger: "加班后想吃夜宵",
        coping_response: "先喝水，再决定要不要吃",
      },
      {
        kind: "marker",
        id: "mk_trip",
        name: "出差",
        event_date: "2026-04-25",
        risk_level: "high",
        note: "提前准备早餐",
        relevant_chapters: null,
        trigger: null,
        coping_response: null,
      },
    ],
  };
}

describe("planner-mirror helpers", () => {
  it("builds process metrics from active chapter + week_view progress", () => {
    expect(buildPlannerProcessMetrics(buildPlan(), buildView())).toEqual([
      {
        key: "早餐蛋白 25 克以上",
        label: "早餐蛋白 25 克以上",
        currentValue: "3/5",
        targetValue: "5/7",
        whyThisGoal: "先稳住白天的饱腹感",
      },
    ]);
  });

  it("builds LifeSign cards from planView.watch_list instead of raw coping plans", () => {
    expect(buildPlannerLifeSigns(buildView())).toEqual([
      {
        id: "ls_night",
        name: "深夜加餐",
        trigger: "加班后想吃夜宵",
        copingResponse: "先喝水，再决定要不要吃",
      },
    ]);
  });

  it("builds event stream rows from planView.map_state.events", () => {
    expect(buildPlannerEventStream(buildView())).toEqual([
      {
        id: "mk_trip",
        date: "2026-04-25",
        description: "月底出差",
        riskLevel: "high",
        isPast: false,
      },
    ]);
  });
});
