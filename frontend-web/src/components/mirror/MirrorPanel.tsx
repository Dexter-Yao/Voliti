// ABOUTME: Mirror 数据面板，展示 Chapter/指标/LifeSign 信息
// ABOUTME: 从 LangGraph Store 同步数据，支持空状态

"use client";

import Image from "next/image";
import { useEffect, useState, useCallback } from "react";
import { RefreshCw, X } from "lucide-react";
import { fetchCoachContext, type CoachContextData, type WitnessCard, type ForwardMarkerSummary } from "@/lib/store-sync";
import { derivePlanPhaseCopy, formatFreshnessLabel } from "@/lib/plan-freshness";
import { InfoTooltip } from "@/components/ui/info-tooltip";

function EmptyState() {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="text-center text-sm text-[#1A1816]/30">
        <p>完成引导流程后查看 Mirror 数据</p>
      </div>
    </div>
  );
}

function PhasePlaceholder({
  headline,
  sublead,
  onRefresh,
}: {
  headline: string;
  sublead: string | null;
  onRefresh: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-[#1A1816]/5 px-4 py-3">
        <h2 className="font-mono-system text-[11px] uppercase tracking-[2px] text-[#1A1816]/40">
          Mirror
        </h2>
        <button
          onClick={onRefresh}
          className="text-[#1A1816]/30 transition-colors hover:text-[#1A1816]/60"
        >
          <RefreshCw className="size-3.5" />
        </button>
      </div>
      <div className="flex flex-1 flex-col items-center justify-center gap-2 p-8 text-center">
        <span className="font-mono-system text-[11px] uppercase tracking-[2px] text-[#B87333]">
          {headline}
        </span>
        {sublead && (
          <p className="font-serif-coach text-sm text-[#1A1816]/60">{sublead}</p>
        )}
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

// high 使用 design-tokens.json 中 --color-risk-red 语义色（#8B3A3A）
const RISK_COLORS: Record<string, string> = {
  high: "text-[#8B3A3A]/70",
  medium: "text-[#B87333]/80",
  low: "text-[#1A1816]/40",
};

const RISK_PILLS: { key: RiskFilter; label: string }[] = [
  { key: "all", label: "全部" },
  { key: "high", label: "高风险" },
  { key: "medium", label: "普通" },
  { key: "low", label: "低风险" },
];

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

  return (
    <div className="space-y-3 border-t border-[#1A1816]/5 pt-4">
      <span className="font-mono-system text-[10px] uppercase tracking-[2px] text-[#B87333]">
        事件日志
      </span>

      <div className="flex flex-wrap gap-1.5">
        {RISK_PILLS.map(({ key, label }) => (
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

  const phaseCopy = derivePlanPhaseCopy(data?.plan, data?.planView);
  if (phaseCopy) {
    return (
      <PhasePlaceholder
        headline={phaseCopy.headline}
        sublead={phaseCopy.sublead}
        onRefresh={refresh}
      />
    );
  }

  const activeChapter =
    data?.plan && data?.planView?.active_chapter_index != null
      ? data.plan.chapters.find(
          (c) => c.chapter_index === data.planView!.active_chapter_index,
        ) ?? null
      : null;

  if (!activeChapter || !data) {
    return <EmptyState />;
  }

  const { plan, copingPlans, dashboardConfig, identityStatement } = data;
  const freshnessLabel = formatFreshnessLabel(data.planView?.week_freshness);

  // Support metrics 目前按 index 对齐到 process_goals（onboarding 后 dashboardConfig
  // 可能仍是空 support_metrics 的 placeholder，此时下方 grid 不渲染）
  const supportMetrics = dashboardConfig?.support_metrics ?? [];
  const cards = data.witnessCards ?? [];
  const PLAN_METRIC_UNIT_MAP: Record<string, string> = {
    weight_kg: "kg",
    weight_lb: "lb",
    bodyfat_pct: "%",
  };
  const northStarUnit =
    dashboardConfig?.north_star?.unit ||
    (plan ? PLAN_METRIC_UNIT_MAP[plan.target.metric] ?? "" : "");

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
              Chapter {activeChapter.chapter_index}
            </span>
            {activeChapter.why_this_chapter && (
              <InfoTooltip label={`第 ${activeChapter.chapter_index} 章的来由`}>
                {activeChapter.why_this_chapter}
              </InfoTooltip>
            )}
            <span className="text-xs text-[#1A1816]/30">
              自 {activeChapter.start_date}
            </span>
            {freshnessLabel && (
              <span className="ml-auto font-mono-system text-[10px] text-[#1A1816]/40">
                {freshnessLabel}
              </span>
            )}
          </div>
          {identityStatement && (
            <p className="font-serif-coach text-sm italic text-[#1A1816]/70">
              &ldquo;{identityStatement}&rdquo;
            </p>
          )}
          {plan?.target_summary && (
            <p className="text-xs text-[#1A1816]/50">{plan.target_summary}</p>
          )}
          <p className="text-xs font-medium text-[#1A1816]/60">{activeChapter.name}</p>
          <p className="text-xs text-[#1A1816]/40">{activeChapter.milestone}</p>
        </div>

        {/* Journey progress bar — 当前 chapter 进度 */}
        {(() => {
          const start = new Date(activeChapter.start_date).getTime();
          const end = new Date(activeChapter.end_date).getTime();
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
                <span>{activeChapter.start_date.slice(5, 10)}</span>
                <span>Day {dayNum}/{totalDays}</span>
              </div>
            </>
          );
        })()}

        {/* North Star metric */}
        {plan && (
          <div className="space-y-2 border-t border-[#1A1816]/5 pt-4">
            <div className="flex items-baseline justify-between">
              <span className="font-mono-system text-[10px] uppercase tracking-[2px] text-[#B87333]">
                ★ {dashboardConfig?.north_star?.label ?? "北极星"}
              </span>
            </div>
            <div className="flex items-end gap-3">
              <span className="font-serif-coach text-[36px] font-semibold text-[#1A1816]">
                {plan.target.baseline}
                <span className="font-mono-system text-xs text-[#B87333]">
                  {" "}{northStarUnit}
                </span>
              </span>
              <span className="text-xs text-[#1A1816]/30">
                → {plan.target.goal_value}
                {northStarUnit}
              </span>
            </div>
          </div>
        )}

        {/* Support metrics —— 与 active chapter 的 process_goals 按序对齐展示 */}
        {supportMetrics.length > 0 && activeChapter.process_goals.length > 0 && (
          <div className="space-y-2 border-t border-[#1A1816]/5 pt-4">
            <div className="grid grid-cols-3 text-center">
              {supportMetrics.slice(0, 3).map((metric, idx) => {
                const processGoal = activeChapter.process_goals[idx] ?? null;
                const target = processGoal
                  ? `${processGoal.weekly_target_days}/${processGoal.weekly_total_days}`
                  : "—";
                const label = processGoal?.name ?? metric.label;
                return (
                  <div
                    key={metric.key}
                    className={idx > 0 ? "border-l border-[#1A1816]/10" : ""}
                  >
                    <div className="font-serif-coach text-xl font-medium text-[#1A1816]">
                      {target}
                    </div>
                    <div className="inline-flex items-center justify-center gap-1">
                      <span className="font-mono-system text-[9px] uppercase tracking-[1px] text-[#1A1816]/40">
                        {label}
                      </span>
                      {processGoal?.why_this_goal && (
                        <InfoTooltip
                          label={`${label} 的来由`}
                          iconSize={10}
                          align={idx === supportMetrics.length - 1 ? "right" : "left"}
                        >
                          {processGoal.why_this_goal}
                        </InfoTooltip>
                      )}
                    </div>
                  </div>
                );
              })}
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
