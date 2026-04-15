// ABOUTME: Mirror 数据面板，展示 Chapter/指标/LifeSign 信息
// ABOUTME: 从 LangGraph Store 同步数据，支持空状态

"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchMirrorData, type MirrorData } from "@/lib/store-sync";
import { getWitnessCards, type WitnessCard } from "@/lib/witness-card-store";
import { RefreshCw, X } from "lucide-react";

function EmptyState() {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="text-center text-sm text-[#1A1816]/30">
        <p>完成引导流程后查看 Mirror 数据</p>
      </div>
    </div>
  );
}

export function MirrorPanel() {
  const [data, setData] = useState<MirrorData | null>(null);
  const [loading, setLoading] = useState(true);
  const [cards, setCards] = useState<WitnessCard[]>([]);
  const [expandedCard, setExpandedCard] = useState<WitnessCard | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchMirrorData();
      setData(result);
    } catch {
      // Silently fail — panel shows empty state
    } finally {
      setLoading(false);
    }
    setCards(getWitnessCards());
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-[#1A1816]/10 border-t-[#B87333]" />
      </div>
    );
  }

  if (!data?.chapter) {
    return <EmptyState />;
  }

  const { chapter, copingPlans, dashboardConfig, identity_statement, goal } = data;
  const processGoalTargets = new Map(
    chapter?.process_goals.map((processGoal) => [processGoal.metric_key, processGoal.target]) ?? [],
  );
  const supportMetrics = dashboardConfig?.support_metrics ?? [];

  return (
    <div className="flex h-full flex-col overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-[#1A1816]/15 [&::-webkit-scrollbar-track]:bg-transparent">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1A1816]/5 px-4 py-3">
        <h2 className="text-sm font-medium text-[#1A1816]/60">Mirror</h2>
        <button
          onClick={refresh}
          className="text-[#1A1816]/30 transition-colors hover:text-[#1A1816]/60"
        >
          <RefreshCw className="size-3.5" />
        </button>
      </div>

      <div className="flex flex-col gap-5 p-4">
        {/* Chapter info */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-[#B87333]">
              Chapter {chapter.chapter_number}
            </span>
            {chapter.start_date && (
              <span className="text-xs text-[#1A1816]/30">
                自 {chapter.start_date}
              </span>
            )}
          </div>
          {identity_statement && (
            <p className="font-serif-coach text-sm italic text-[#1A1816]/70">
              &ldquo;{identity_statement}&rdquo;
            </p>
          )}
          {goal?.description && (
            <p className="text-xs text-[#1A1816]/50">{goal.description}</p>
          )}
          {chapter.title && (
            <p className="text-xs font-medium text-[#1A1816]/60">{chapter.title}</p>
          )}
          {chapter.milestone && (
            <p className="text-xs text-[#1A1816]/40">{chapter.milestone}</p>
          )}
        </div>

        {/* North Star metric */}
        {dashboardConfig?.north_star && (
          <div className="space-y-2 border-t border-[#1A1816]/5 pt-4">
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-[#1A1816]/60">
                {dashboardConfig.north_star.label}
              </span>
            </div>
            <div className="flex items-end gap-3">
              {goal?.north_star_target ? (
                <span className="text-2xl font-semibold text-[#1A1816]">
                  {goal.north_star_target.baseline}
                  <span className="text-sm font-normal text-[#1A1816]/40">
                    {goal.north_star_target.unit}
                  </span>
                </span>
              ) : (
                <span className="text-2xl font-semibold text-[#1A1816]">—</span>
              )}
              {goal?.north_star_target && (
                <span className="text-xs text-[#1A1816]/30">
                  → {goal.north_star_target.target}
                  {goal.north_star_target.unit}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Support metrics */}
        {supportMetrics.length > 0 && (
          <div className="space-y-2 border-t border-[#1A1816]/5 pt-4">
            <span className="text-xs font-medium text-[#1A1816]/40">
              辅助指标
            </span>
            <div className="grid gap-2">
              {supportMetrics.map((metric) => (
                <div
                  key={metric.key}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-[#1A1816]/60">{metric.label}</span>
                  <span className="font-medium text-[#1A1816]">
                    {processGoalTargets.get(metric.key) ?? "—"}
                    {metric.unit && (
                      <span className="text-xs font-normal text-[#1A1816]/40">
                        {" "}
                        {metric.unit}
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Coping plans / LifeSign */}
        {copingPlans.length > 0 && (
          <div className="space-y-2 border-t border-[#1A1816]/5 pt-4">
            <span className="text-xs font-medium text-[#1A1816]/40">
              LifeSign 方案
            </span>
            <div className="flex flex-col gap-1.5">
              {copingPlans.map((plan, i) => (
                <div key={i} className="text-xs">
                  <span className="text-[#1A1816]/60">{plan.trigger}</span>
                  {plan.plan && (
                    <span className="text-[#1A1816]/40"> → {plan.plan}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Witness Card gallery */}
        {cards.length > 0 && (
          <div className="space-y-2 border-t border-[#1A1816]/5 pt-4">
            <span className="text-xs font-medium text-[#1A1816]/40">
              见证卡
            </span>
            <div className="grid grid-cols-3 gap-1.5">
              {cards.map((card) => (
                <button
                  key={card.id}
                  onClick={() => setExpandedCard(card)}
                  className="aspect-square overflow-hidden bg-[#1A1816]/5 transition-opacity hover:opacity-80"
                >
                  <img
                    src={card.src}
                    alt={card.alt}
                    className="h-full w-full object-cover"
                  />
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Expanded Witness Card overlay */}
      {expandedCard && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#1A1816]/40"
          onClick={() => setExpandedCard(null)}
        >
          <div className="relative max-h-[80vh] max-w-[90vw]">
            <button
              onClick={() => setExpandedCard(null)}
              className="absolute -top-3 -right-3 flex h-8 w-8 items-center justify-center rounded-full bg-white shadow-md"
            >
              <X className="size-4" />
            </button>
            <img
              src={expandedCard.src}
              alt={expandedCard.alt}
              className="max-h-[80vh] max-w-full object-contain"
            />
          </div>
        </div>
      )}
    </div>
  );
}
