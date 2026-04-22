// ABOUTME: plan-freshness 纯函数单测
// ABOUTME: 覆盖 freshness 三态 × plan_phase 三态的文案输出

import { describe, expect, it } from "vitest";

import type { PlanDocumentData, PlanViewData } from "./mirror-contract";
import { derivePlanPhaseCopy, formatFreshnessLabel } from "./plan-freshness";

describe("formatFreshnessLabel", () => {
  it("returns null for fresh — user just interacted, no echo needed", () => {
    expect(
      formatFreshnessLabel({ days_since_update: 0, level: "fresh" }),
    ).toBeNull();
  });

  it("returns days-prefixed label for stale", () => {
    expect(
      formatFreshnessLabel({ days_since_update: 2, level: "stale" }),
    ).toBe("2 天前记录");
  });

  it("returns gentle natural-language label for very_stale — no catastrophic framing", () => {
    expect(
      formatFreshnessLabel({ days_since_update: 9, level: "very_stale" }),
    ).toBe("有一段时间没聊了");
  });

  it("returns null when freshness missing (plan has no current_week yet)", () => {
    expect(formatFreshnessLabel(null)).toBeNull();
    expect(formatFreshnessLabel(undefined)).toBeNull();
  });

  it("stale with days=0 clamps up to at least 1 (guards against same-day boundary)", () => {
    expect(
      formatFreshnessLabel({ days_since_update: 0, level: "stale" }),
    ).toBe("1 天前记录");
  });
});

function buildPlan(startedAt: string): PlanDocumentData {
  return {
    plan_id: "plan_test",
    status: "active",
    version: 1,
    predecessor_version: null,
    supersedes_plan_id: null,
    change_summary: null,
    target_summary: "两个月减 10 斤",
    overall_narrative: "测试用 narrative",
    started_at: startedAt,
    planned_end_at: "2026-06-01T00:00:00+08:00",
    created_at: startedAt,
    revised_at: startedAt,
    target: {
      metric: "weight_kg",
      baseline: 70,
      goal_value: 65,
      duration_weeks: 8,
      rate_kg_per_week: 0.625,
    },
    chapters: [],
    linked_lifesigns: [],
    linked_markers: [],
    current_week: null,
  };
}

function buildView(phase: PlanViewData["plan_phase"]): PlanViewData {
  return {
    plan_phase: phase,
    active_chapter_index: phase === "in_chapter" ? 1 : null,
    week_index: 1,
    day_progress: [0, 56],
    active_chapter_day_progress: [0, 0],
    days_left_in_chapter: 0,
    map_state: { flag_ratio: 0, events: [] },
    week_view: [],
    week_freshness: null,
    day_template: [],
    watch_list: [],
  };
}

describe("derivePlanPhaseCopy", () => {
  it("returns null for in_chapter — caller renders the normal Chapter block", () => {
    const copy = derivePlanPhaseCopy(buildPlan("2026-04-01T00:00:00+08:00"), buildView("in_chapter"));
    expect(copy).toBeNull();
  });

  it("before_start computes days until launch", () => {
    const plan = buildPlan("2026-05-01T00:00:00+08:00");
    const now = new Date("2026-04-25T00:00:00+08:00");
    const copy = derivePlanPhaseCopy(plan, buildView("before_start"), now);
    expect(copy).not.toBeNull();
    expect(copy!.headline).toBe("方案 · 等待启航");
    expect(copy!.sublead).toMatch(/还有 \d+ 天/);
  });

  it("before_start on the very start day says imminent entry, not 0-day countdown", () => {
    const plan = buildPlan("2026-05-01T00:00:00+08:00");
    const now = new Date("2026-05-01T00:00:00+08:00");
    const copy = derivePlanPhaseCopy(plan, buildView("before_start"), now);
    expect(copy!.sublead).toBe("即将进入第一章");
  });

  it("after_end reflects completion without judging", () => {
    const copy = derivePlanPhaseCopy(
      buildPlan("2026-04-01T00:00:00+08:00"),
      buildView("after_end"),
    );
    expect(copy).not.toBeNull();
    expect(copy!.headline).toBe("方案 · 本段已走完");
    expect(copy!.sublead).toBe("等 Coach 一起定下一段");
  });

  it("returns null when plan or view is missing (defensive — API not populated)", () => {
    expect(derivePlanPhaseCopy(null, buildView("in_chapter"))).toBeNull();
    expect(derivePlanPhaseCopy(buildPlan("2026-04-01T00:00:00+08:00"), null)).toBeNull();
  });
});
