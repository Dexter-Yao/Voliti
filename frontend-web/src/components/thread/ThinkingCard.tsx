// ABOUTME: Coach 思维过程可折叠卡片
// ABOUTME: 展示 strategy/observations/actions，默认折叠

"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Brain } from "lucide-react";
import type { CoachThinking } from "@/lib/stream-sanitize";

export function ThinkingCard({ thinking }: { thinking: CoachThinking }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-[#1A1816]/5 bg-[#F4F0E8]/50">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-[#1A1816]/40 hover:text-[#1A1816]/60"
      >
        <Brain className="size-3.5" />
        <span>Coach Thinking</span>
        {open ? (
          <ChevronDown className="ml-auto size-3.5" />
        ) : (
          <ChevronRight className="ml-auto size-3.5" />
        )}
      </button>

      {open && (
        <div className="space-y-2 border-t border-[#1A1816]/5 px-3 py-2 text-xs text-[#1A1816]/60">
          {thinking.strategy && (
            <div>
              <span className="font-medium text-[#1A1816]/50">Strategy: </span>
              {thinking.strategy}
            </div>
          )}
          {thinking.observations.length > 0 && (
            <div>
              <span className="font-medium text-[#1A1816]/50">Observations:</span>
              <ul className="ml-4 list-disc">
                {thinking.observations.map((obs, i) => (
                  <li key={i}>{obs}</li>
                ))}
              </ul>
            </div>
          )}
          {thinking.actions.length > 0 && (
            <div>
              <span className="font-medium text-[#1A1816]/50">Actions:</span>
              <ul className="ml-4 list-disc">
                {thinking.actions.map((act, i) => (
                  <li key={i}>{act}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
