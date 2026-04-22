// ABOUTME: Mirror 的 Planner 投影纯函数
// ABOUTME: active-plan 区块统一消费 plan 与 planView，不再依赖 raw store 派生

import type { PlanDocumentData, PlanViewData } from "./mirror-contract";

export interface PlannerProcessMetric {
  key: string;
  label: string;
  currentValue: string;
  targetValue: string;
  whyThisGoal: string | null;
}

export interface PlannerLifeSignCard {
  id: string;
  name: string;
  trigger: string | null;
  copingResponse: string | null;
}

export interface PlannerEventRow {
  id: string;
  date: string;
  description: string;
  riskLevel: string;
  isPast: boolean;
}

export function getActiveChapter(
  plan: PlanDocumentData | null,
  planView: PlanViewData | null,
) {
  if (!plan || planView?.active_chapter_index == null) {
    return null;
  }
  return (
    plan.chapters.find(
      (chapter) => chapter.chapter_index === planView.active_chapter_index,
    ) ?? null
  );
}

export function buildPlannerProcessMetrics(
  plan: PlanDocumentData | null,
  planView: PlanViewData | null,
): PlannerProcessMetric[] {
  const activeChapter = getActiveChapter(plan, planView);
  if (!activeChapter || !planView) return [];

  const statusByGoalName = new Map(
    planView.week_view.map((status) => [status.goal_name, status]),
  );
  return activeChapter.process_goals.map((goal) => {
    const status = statusByGoalName.get(goal.name);
    return {
      key: goal.name,
      label: goal.name,
      currentValue: status
        ? `${status.days_met}/${status.days_expected}`
        : "—",
      targetValue: `${goal.weekly_target_days}/${goal.weekly_total_days}`,
      whyThisGoal: goal.why_this_goal,
    };
  });
}

export function buildPlannerLifeSigns(
  planView: PlanViewData | null,
): PlannerLifeSignCard[] {
  if (!planView) return [];
  return planView.watch_list
    .filter((item) => item.kind === "lifesign")
    .map((item) => ({
      id: item.id,
      name: item.name,
      trigger: item.trigger,
      copingResponse: item.coping_response,
    }));
}

export function buildPlannerEventStream(
  planView: PlanViewData | null,
): PlannerEventRow[] {
  if (!planView) return [];
  return [...planView.map_state.events]
    .map((event) => ({
      id: event.id,
      date: event.event_date,
      description: event.description ?? event.name,
      riskLevel: event.risk_level ?? "medium",
      isPast: event.is_past,
    }))
    .sort((left, right) => Date.parse(right.date) - Date.parse(left.date));
}
