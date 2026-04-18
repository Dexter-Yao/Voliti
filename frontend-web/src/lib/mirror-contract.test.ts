// ABOUTME: Mirror Store 契约测试
// ABOUTME: 使用共享 fixtures 验证 chapter、goal、dashboardConfig 的读取边界

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import {
  buildAcceptedWitnessCardsFromStoreItems,
  buildMirrorDataFromStoreValues,
} from "./mirror-contract";

function loadFixture(name: string): Record<string, unknown> {
  const path = resolve(process.cwd(), "../tests/contracts/fixtures/store", name);
  return JSON.parse(readFileSync(path, "utf-8")) as Record<string, unknown>;
}

function makeGoalFixture(): Record<string, unknown> {
  return {
    version: "1",
    content: [
      "{",
      '  "id": "goal_001",',
      '  "description": "12 周内从 75kg 减至 70kg",',
      '  "north_star_target": {"key": "weight_trend", "baseline": 75, "target": 70, "unit": "kg"},',
      '  "start_date": "2026-04-09T10:00:00Z",',
      '  "target_date": "2026-07-02T10:00:00Z",',
      '  "status": "active"',
      "}",
    ],
    created_at: "2026-04-09T10:00:00Z",
    modified_at: "2026-04-09T10:00:00Z",
  };
}

describe("buildMirrorDataFromStoreValues", () => {
  it("reads chapter, goal, profile, and dashboard config from their canonical store items", () => {
    const data = buildMirrorDataFromStoreValues({
      chapterValue: loadFixture("chapter_current.value.json"),
      dashboardConfigValue: loadFixture("dashboard_config.value.json"),
      goalValue: makeGoalFixture(),
      profileValue: loadFixture("profile_context.value.json"),
    });

    expect(data.chapter?.title).toBe("建立工作日饮食节奏");
    expect(data.goal?.description).toContain("减至");
    expect(data.identity_statement).toContain("清醒选择");
    expect(data.dashboardConfig?.north_star.label).toBe("体重趋势");
    expect(data.dashboardConfig?.support_metrics[0]?.label).toBe("达标天数");
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
