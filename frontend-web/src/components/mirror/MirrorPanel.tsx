// ABOUTME: Mirror 数据面板，展示 Chapter/指标/LifeSign 信息
// ABOUTME: 从 LangGraph Store 同步数据，支持空状态

"use client";

import Image from "next/image";
import { useEffect, useState, useCallback } from "react";
import { RefreshCw, X } from "lucide-react";
import { fetchCoachContext, type CoachContextData, type WitnessCard, type ForwardMarkerSummary } from "@/lib/store-sync";

function EmptyState() {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="text-center text-sm text-[#1A1816]/30">
        <p>完成引导流程后查看 Mirror 数据</p>
      </div>
    </div>
  );
}

type RiskFilter = "all" | "high" | "medium" | "low";

const RISK_LABELS: Record<string, string> = {
  high: "高",
  medium: "中",
  low: "低",
};

const RISK_COLORS: Record<string, string> = {
  high: "text-red-500/70",
  medium: "text-[#B87333]/80",
  low: "text-[#1A1816]/40",
};

function formatMarkerDate(dateStr: string): string {
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return dateStr;
  return `${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function EventStream({ markers }: { markers: ForwardMarkerSummary[] }) {
  const [filter, setFilter] = useState<RiskFilter>("all");

  const visible = markers.filter(
    (m) => filter === "all" || m.riskLevel === filter,
  );

  const pills: { key: RiskFilter; label: string }[] = [
    { key: "all", label: "全部" },
    { key: "high", label: "高风险" },
    { key: "medium", label: "普通" },
    { key: "low", label: "低风险" },
  ];

  return (
    <div className="space-y-3 border-t border-[#1A1816]/5 pt-4">
      <span className="font-mono-system text-[10px] uppercase tracking-[2px] text-[#B87333]">
        事件日志
      </span>

      <div className="flex flex-wrap gap-1.5">
        {pills.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`rounded-full px-2.5 py-0.5 font-mono-system text-[9px] uppercase tracking-[1px] transition-colors ${
              filter === key
                ? "bg-[#B87333] text-white"
                : "bg-[#1A1816]/5 text-[#1A1816]/40 hover:bg-[#1A1816]/10"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <p className="text-[11px] text-[#1A1816]/30">暂无记录</p>
      ) : (
        <div className="flex flex-col gap-0">
          {visible.map((marker, idx) => (
            <div key={marker.id} className="flex gap-2.5">
              <div className="flex flex-col items-center">
                <div
                  className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${
                    marker.isPast ? "bg-[#1A1816]/20" : "bg-[#B87333]"
                  }`}
                />
                {idx < visible.length - 1 && (
                  <div className="w-px flex-1 bg-[#1A1816]/8 my-0.5" />
                )}
              </div>
              <div className="pb-3 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono-system text-[9px] text-[#1A1816]/30">
                    {formatMarkerDate(marker.date)}
                  </span>
                  <span
                    className={`font-mono-system text-[9px] uppercase ${RISK_COLORS[marker.riskLevel] ?? "text-[#1A1816]/40"}`}
                  >
                    {RISK_LABELS[marker.riskLevel] ?? marker.riskLevel}
                  </span>
                  {marker.isPast && (
                    <span className="font-mono-system text-[9px] text-[#1A1816]/20">
                      已过
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-[11px] leading-4 text-[#1A1816]/60">
                  {marker.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function MirrorPanel() {
  const [data, setData] = useState<CoachContextData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedCard, setExpandedCard] = useState<WitnessCard | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCoachContext();
      setData(result);
    } catch (err) {
      setError(
        err instanceof Error && err.message
          ? err.message
          : "暂时无法读取 Mirror，请稍后重试。",
      );
    } finally {
      setLoading(false);
    }
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

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="max-w-[240px] text-center">
          <p className="text-sm leading-6 text-[#1A1816]/60">{error}</p>
          <button
            onClick={refresh}
            className="mt-4 text-xs text-[#B87333] transition-colors hover:text-[#965f29]"
          >
            重新加载
          </button>
        </div>
      </div>
    );
  }

  if (!data?.mirrorData.chapter) {
    return <EmptyState />;
  }

  const { chapter, copingPlans, dashboardConfig, identity_statement, goal } =
    data.mirrorData;
  const processGoalTargets = new Map(
    chapter?.process_goals.map((processGoal) => [processGoal.metric_key, processGoal.target]) ?? [],
  );
  const supportMetrics = dashboardConfig?.support_metrics ?? [];
  const cards = data.witnessCards ?? [];

  return (
    <div className="flex h-full flex-col overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-[#1A1816]/15 [&::-webkit-scrollbar-track]:bg-transparent">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1A1816]/5 px-4 py-3">
        <h2 className="font-mono-system text-[11px] uppercase tracking-[2px] text-[#1A1816]/40">Mirror</h2>
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
            <span className="font-mono-system text-[10px] uppercase tracking-[2px] text-[#B87333]">
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

        {/* Journey progress bar */}
        {chapter.start_date && chapter.planned_end_date && (() => {
          const start = new Date(chapter.start_date).getTime();
          const end = new Date(chapter.planned_end_date).getTime();
          const now = Date.now();
          const total = end - start;
          const elapsed = now - start;
          const pct = total > 0 ? Math.max(0, Math.min(100, (elapsed / total) * 100)) : 0;
          const dayNum = Math.max(1, Math.ceil(elapsed / (1000 * 60 * 60 * 24)));
          const totalDays = Math.max(1, Math.ceil(total / (1000 * 60 * 60 * 24)));
          return (
            <>
              <div className="relative h-[2px] bg-[#1A1816]/10">
                <div className="absolute left-0 top-0 h-full bg-[#B87333]" style={{ width: `${pct}%` }} />
                <div className="absolute top-[-3px] h-2 w-2 rounded-full bg-[#B87333]" style={{ left: `${pct}%` }} />
              </div>
              <div className="mt-1 flex justify-between font-mono-system text-[8px] text-[#1A1816]/30">
                <span>{chapter.start_date.slice(5, 10)}</span>
                <span>Day {dayNum}/{totalDays}</span>
              </div>
            </>
          );
        })()}

        {/* North Star metric */}
        {dashboardConfig?.north_star && (
          <div className="space-y-2 border-t border-[#1A1816]/5 pt-4">
            <div className="flex items-baseline justify-between">
              <span className="font-mono-system text-[10px] uppercase tracking-[2px] text-[#B87333]">
                ★ {dashboardConfig.north_star.label}
              </span>
            </div>
            <div className="flex items-end gap-3">
              {goal?.north_star_target ? (
                <span className="font-serif-coach text-[36px] font-semibold text-[#1A1816]">
                  {goal.north_star_target.baseline}
                  <span className="font-mono-system text-xs text-[#B87333]">
                    {" "}{goal.north_star_target.unit}
                  </span>
                </span>
              ) : (
                <span className="font-serif-coach text-[36px] font-semibold text-[#1A1816]">—</span>
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
            <div className="grid grid-cols-3 text-center">
              {supportMetrics.map((metric, idx) => (
                <div
                  key={metric.key}
                  className={idx > 0 ? "border-l border-[#1A1816]/10" : ""}
                >
                  <div className="font-serif-coach text-xl font-medium text-[#1A1816]">
                    {processGoalTargets.get(metric.key) ?? "—"}
                  </div>
                  <div className="font-mono-system text-[9px] uppercase tracking-[1px] text-[#1A1816]/40">
                    {metric.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Coping plans / LifeSign */}
        {copingPlans.length > 0 && (
          <div className="space-y-2 border-t border-[#1A1816]/5 pt-4">
            <span className="font-mono-system text-xs uppercase tracking-[2px] text-[#B87333]">
              LifeSign
            </span>
            <div className="flex flex-col gap-3">
              {copingPlans.map((plan, i) => (
                <div key={i}>
                  <div className="text-xs">
                    <span className="font-mono-system text-[10px] text-[#B87333]">IF </span>
                    <span className="font-serif-coach text-[#1A1816]/60">{plan.trigger}</span>
                  </div>
                  {plan.coping_response && (
                    <div className="mt-0.5 text-xs">
                      <span className="font-mono-system text-[10px] text-[#B87333]">THEN </span>
                      <span className="font-serif-coach text-[#1A1816]/60">{plan.coping_response}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Event stream */}
        {(data.allMarkers?.length ?? 0) > 0 && (
          <EventStream markers={data.allMarkers} />
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
                  <Image
                    src={card.src}
                    alt={card.alt}
                    width={512}
                    height={512}
                    unoptimized
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
            <Image
              src={expandedCard.src}
              alt={expandedCard.alt}
              width={1200}
              height={1200}
              unoptimized
              className="max-h-[80vh] max-w-full object-contain"
            />
          </div>
        </div>
      )}
    </div>
  );
}
