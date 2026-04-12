// ABOUTME: Mirror 数据面板，展示 Chapter/指标/LifeSign 信息
// ABOUTME: 从 LangGraph Store 同步数据，支持空状态

"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchMirrorData, type MirrorData } from "@/lib/store-sync";
import { getWitnessCards, type WitnessCard } from "@/lib/witness-card-store";
import { RefreshCw, X } from "lucide-react";

function NorthStarChart({ history }: { history: number[] }) {
  if (history.length === 0) return null;
  const max = Math.max(...history);
  const min = Math.min(...history);
  const range = max - min || 1;

  return (
    <div className="flex h-12 items-end gap-0.5">
      {history.slice(-7).map((val, i) => (
        <div
          key={i}
          className="flex-1 bg-[#B87333]/60"
          style={{
            height: `${Math.max(((val - min) / range) * 100, 8)}%`,
          }}
        />
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="text-center text-sm text-[#1A1816]/30">
        <p>Complete onboarding to see your Mirror data</p>
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

  const { chapter, copingPlans } = data;

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
                since {chapter.start_date}
              </span>
            )}
          </div>
          {chapter.identity_declaration && (
            <p className="font-serif-coach text-sm italic text-[#1A1816]/70">
              &ldquo;{chapter.identity_declaration}&rdquo;
            </p>
          )}
          {chapter.goal && (
            <p className="text-xs text-[#1A1816]/50">{chapter.goal}</p>
          )}
        </div>

        {/* North Star metric */}
        {chapter.north_star && (
          <div className="space-y-2 border-t border-[#1A1816]/5 pt-4">
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-medium text-[#1A1816]/60">
                {chapter.north_star.metric}
              </span>
              {chapter.north_star.delta != null && (
                <span
                  className={`text-xs font-medium ${chapter.north_star.delta <= 0 ? "text-green-600" : "text-red-500"}`}
                >
                  {chapter.north_star.delta > 0 ? "+" : ""}
                  {chapter.north_star.delta}
                  {chapter.north_star.unit}
                </span>
              )}
            </div>
            <div className="flex items-end gap-3">
              {chapter.north_star.current_value != null && (
                <span className="text-2xl font-semibold text-[#1A1816]">
                  {chapter.north_star.current_value}
                  <span className="text-sm font-normal text-[#1A1816]/40">
                    {chapter.north_star.unit}
                  </span>
                </span>
              )}
              {chapter.north_star.target_value != null && (
                <span className="text-xs text-[#1A1816]/30">
                  → {chapter.north_star.target_value}
                  {chapter.north_star.unit}
                </span>
              )}
            </div>
            {chapter.north_star.history?.length > 0 && (
              <NorthStarChart history={chapter.north_star.history} />
            )}
          </div>
        )}

        {/* Support metrics */}
        {chapter.support_metrics?.length > 0 && (
          <div className="space-y-2 border-t border-[#1A1816]/5 pt-4">
            <span className="text-xs font-medium text-[#1A1816]/40">
              Support Metrics
            </span>
            <div className="grid gap-2">
              {chapter.support_metrics.map((m, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-[#1A1816]/60">{m.metric}</span>
                  <span className="font-medium text-[#1A1816]">
                    {m.current_value ?? "—"}
                    <span className="text-xs font-normal text-[#1A1816]/40">
                      {m.unit}
                    </span>
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
              LifeSign Plans
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
              Witness Cards
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
