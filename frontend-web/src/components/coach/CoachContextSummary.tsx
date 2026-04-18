// ABOUTME: 教练上下文摘要卡片
// ABOUTME: 将首周起点、当前高风险场景和最近前瞻事件压缩为用户可见的最小上下文

import type { CoachContextData } from "@/lib/store-sync";

function formatMarkerDate(date: string): string {
  const parsed = Date.parse(date);
  if (!Number.isFinite(parsed)) {
    return date;
  }
  return new Date(parsed).toLocaleDateString("zh-CN", {
    month: "short",
    day: "numeric",
  });
}

export function CoachContextSummary({
  context,
  compact = false,
}: {
  context: CoachContextData;
  compact?: boolean;
}) {
  const firstPlan = context.mirrorData.copingPlans[0] ?? null;
  const firstMarker = context.upcomingMarkers[0] ?? null;
  const firstProcessGoal = context.mirrorData.chapter?.process_goals[0] ?? null;
  const cards = [
    {
      label: "本周成功定义",
      value:
        context.mirrorData.chapter?.milestone
        || context.mirrorData.chapter?.title
        || "先把这一阶段的节奏建立起来。",
    },
    {
      label: "当前高风险场景",
      value:
        firstPlan?.trigger
        || "教练会继续帮你识别最容易失守的时刻。",
    },
    {
      label: firstMarker ? "最近前瞻事件" : "下一步聚焦",
      value: firstMarker
        ? `${formatMarkerDate(firstMarker.date)} · ${firstMarker.description}`
        : firstPlan?.coping_response || firstProcessGoal?.description || "先把第一步做得足够轻。",
    },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-3">
      {cards.map((card) => (
        <div
          key={card.label}
          className="border border-[#1A1816]/8 bg-[#1A1816]/[0.03] px-4 py-3 text-left"
        >
          <p className="font-mono-system text-[10px] uppercase tracking-[2px] text-[#B87333]">
            {card.label}
          </p>
          <p
            className={`mt-2 text-[#1A1816]/70 ${
              compact
                ? "text-xs leading-5"
                : "font-serif-coach text-sm leading-6"
            }`}
          >
            {card.value}
          </p>
        </div>
      ))}
    </div>
  );
}
