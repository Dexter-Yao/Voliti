// ABOUTME: mirror-contract 纯函数单测
// ABOUTME: 覆盖 copingPlans / identity / witness card 三类解析辅助

import { describe, expect, it } from "vitest";

import {
  buildAcceptedWitnessCardsFromStoreItems,
  parseCopingPlans,
  parseIdentityStatement,
} from "./mirror-contract";

describe("parseCopingPlans", () => {
  it("extracts trigger and response from arrow-delimited bullets", () => {
    const md = [
      "# LifeSign Index",
      "- 下班压力大想吃零食 → 泡茶 + 阳台 3 分钟",
      "* 周末聚餐后 → 提前吃轻食垫底",
    ].join("\n");

    const plans = parseCopingPlans(md);

    expect(plans).toEqual([
      { trigger: "下班压力大想吃零食", coping_response: "泡茶 + 阳台 3 分钟" },
      { trigger: "周末聚餐后", coping_response: "提前吃轻食垫底" },
    ]);
  });

  it("keeps bullets without arrows as trigger-only entries", () => {
    const plans = parseCopingPlans("- 保留一个场景待后续补充");
    expect(plans).toEqual([
      { trigger: "保留一个场景待后续补充", coping_response: "" },
    ]);
  });

  it("returns empty array for markdown without list items", () => {
    expect(parseCopingPlans("# LifeSign Index\n（暂无）")).toEqual([]);
  });
});

describe("parseIdentityStatement", () => {
  it("reads bullet-prefixed identity_statement line", () => {
    const md = [
      "# Profile",
      "## Identity",
      "- name: 嘉文",
      "- identity_statement: 一个在忙碌里也能对自己身体保持觉察的人",
    ].join("\n");
    expect(parseIdentityStatement(md)).toBe(
      "一个在忙碌里也能对自己身体保持觉察的人",
    );
  });

  it("returns null when identity_statement absent", () => {
    expect(parseIdentityStatement("# Profile\n- name: ?")).toBeNull();
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
