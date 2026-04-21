// ABOUTME: Plan 时间回声与 phase 文案
// ABOUTME: 时间信号用自然语言，不用量化警告——避免在失控螺旋边缘制造催促感

import type { PlanDocumentData, PlanViewData, PlanViewWeekFreshness } from "./mirror-contract";

/**
 * 把 week_freshness 翻译为一行轻量文案。
 *
 * fresh 态返回 null——用户刚聊完就看到"今晨更新"像系统回执，冗余。
 * stale / very_stale 用中性、非评判的语气：不使用"整整一周未更新"这类
 * 容易触发灾难化叙述的表达。
 */
export function formatFreshnessLabel(
  freshness: PlanViewWeekFreshness | null | undefined,
): string | null {
  if (!freshness) return null;
  switch (freshness.level) {
    case "fresh":
      return null;
    case "stale": {
      const days = Math.max(1, freshness.days_since_update);
      return `${days} 天前记录`;
    }
    case "very_stale":
      return "有一段时间没聊了";
    default:
      return null;
  }
}

/**
 * 根据 plan_phase 推导 MirrorPanel 顶部的位置感文案。
 *
 * before_start：方案未启航；显示距 started_at 的倒计时
 * in_chapter：当前正在某一章（返回 null，走主流程渲染 Chapter 信息块）
 * after_end：方案本段已走完，等待下一段
 *
 * 返回 null 表示"按现有 Chapter 信息块渲染"，调用方按正常流程走。
 */
export interface PlanPhaseCopy {
  headline: string;
  sublead: string | null;
}

export function derivePlanPhaseCopy(
  plan: PlanDocumentData | null | undefined,
  planView: PlanViewData | null | undefined,
  now: Date = new Date(),
): PlanPhaseCopy | null {
  if (!plan || !planView) return null;

  if (planView.plan_phase === "before_start") {
    const startTs = Date.parse(plan.started_at);
    const daysUntilStart = Number.isFinite(startTs)
      ? Math.max(0, Math.ceil((startTs - now.getTime()) / (1000 * 60 * 60 * 24)))
      : null;
    return {
      headline: "方案 · 等待启航",
      sublead:
        daysUntilStart !== null && daysUntilStart > 0
          ? `还有 ${daysUntilStart} 天进入第一章`
          : "即将进入第一章",
    };
  }

  if (planView.plan_phase === "after_end") {
    return {
      headline: "方案 · 本段已走完",
      sublead: "等 Coach 一起定下一段",
    };
  }

  return null;
}
