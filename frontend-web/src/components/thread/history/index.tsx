// ABOUTME: 对话历史侧边栏，按天分组显示 Thread 列表
// ABOUTME: 支持点击切换 Thread，今天的日期标题高亮

import { Button } from "@/components/ui/button";
import { useThreads } from "@/providers/Thread";
import { Thread } from "@langchain/langgraph-sdk";
import { useEffect, useMemo } from "react";
import { getContentString } from "../utils";
import { useQueryState } from "nuqs";
import { Skeleton } from "@/components/ui/skeleton";
import { isThreadSealed } from "@/lib/thread-utils";
import { getTodayDateString } from "@/lib/user";

interface DateGroup {
  date: string;
  label: string;
  isToday: boolean;
  threads: Thread[];
}

function groupThreadsByDate(threads: Thread[]): DateGroup[] {
  const today = getTodayDateString();
  const groups = new Map<string, Thread[]>();

  for (const thread of threads) {
    const date =
      (thread.metadata as Record<string, unknown>)?.date as string ??
      thread.created_at?.slice(0, 10) ??
      "unknown";
    const existing = groups.get(date) ?? [];
    existing.push(thread);
    groups.set(date, existing);
  }

  // Sort dates descending (newest first)
  const sortedDates = [...groups.keys()].sort((a, b) => b.localeCompare(a));

  return sortedDates.map((date) => ({
    date,
    label: date === today ? "Today" : formatDateLabel(date),
    isToday: date === today,
    threads: groups.get(date)!,
  }));
}

function formatDateLabel(dateStr: string): string {
  try {
    const date = new Date(dateStr + "T00:00:00");
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const yesterdayStr = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, "0")}-${String(yesterday.getDate()).padStart(2, "0")}`;
    if (dateStr === yesterdayStr) {
      return "Yesterday";
    }

    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function ThreadItem({
  thread,
  isActive,
  onClick,
}: {
  thread: Thread;
  isActive: boolean;
  onClick: () => void;
}) {
  const sealed = isThreadSealed(thread);
  let itemText = "New conversation";
  if (
    typeof thread.values === "object" &&
    thread.values &&
    "messages" in thread.values &&
    Array.isArray(thread.values.messages) &&
    thread.values.messages?.length > 0
  ) {
    const firstMessage = thread.values.messages[0];
    const text = getContentString(firstMessage.content);
    if (text) itemText = text;
  }

  return (
    <Button
      variant="ghost"
      className={`w-full justify-start text-left font-normal text-sm ${isActive ? "bg-[#1A1816]/5" : ""} ${sealed ? "opacity-60" : ""}`}
      onClick={onClick}
    >
      <p className="truncate">{itemText}</p>
    </Button>
  );
}

function ThreadHistoryLoading() {
  return (
    <div className="flex flex-col gap-1 px-2">
      {Array.from({ length: 10 }).map((_, i) => (
        <Skeleton key={`skeleton-${i}`} className="h-9 w-full" />
      ))}
    </div>
  );
}

export default function ThreadHistory({
  onThreadSelect,
}: {
  onThreadSelect?: (threadId: string) => void;
}) {
  const [threadId, setThreadId] = useQueryState("threadId");
  const { getThreads, threads, setThreads, threadsLoading, setThreadsLoading } =
    useThreads();

  useEffect(() => {
    if (typeof window === "undefined") return;
    setThreadsLoading(true);
    getThreads()
      .then(setThreads)
      .catch(console.error)
      .finally(() => setThreadsLoading(false));
  }, [getThreads, setThreads, setThreadsLoading]);

  const dateGroups = useMemo(() => groupThreadsByDate(threads), [threads]);

  const handleThreadClick = (id: string) => {
    onThreadSelect?.(id);
    if (id !== threadId) {
      setThreadId(id);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-[#1A1816]/15 [&::-webkit-scrollbar-track]:bg-transparent">
      <div className="px-4 py-3">
        <h2 className="text-sm font-medium text-[#1A1816]/60">History</h2>
      </div>

      {threadsLoading ? (
        <ThreadHistoryLoading />
      ) : dateGroups.length === 0 ? (
        <div className="px-4 text-sm text-[#1A1816]/40">
          No conversations yet
        </div>
      ) : (
        <div className="flex flex-col gap-3 px-2 pb-4">
          {dateGroups.map((group) => (
            <div key={group.date}>
              <div className="px-2 pb-1">
                <span
                  className={`text-xs font-medium ${
                    group.isToday
                      ? "text-[#B87333]"
                      : "text-[#1A1816]/40"
                  }`}
                >
                  {group.label}
                </span>
              </div>
              <div className="flex flex-col gap-0.5">
                {group.threads.map((t) => (
                  <ThreadItem
                    key={t.thread_id}
                    thread={t}
                    isActive={t.thread_id === threadId}
                    onClick={() => handleThreadClick(t.thread_id)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
