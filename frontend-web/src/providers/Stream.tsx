// ABOUTME: Stream provider，封装 LangGraph useStream hook
// ABOUTME: 预创建/复用每日 Thread，注入 user_id + date metadata

import React, {
  createContext,
  useContext,
  ReactNode,
  useEffect,
  useRef,
} from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import { type Message } from "@langchain/langgraph-sdk";
import {
  uiMessageReducer,
  isUIMessage,
  isRemoveUIMessage,
  type UIMessage,
  type RemoveUIMessage,
} from "@langchain/langgraph-sdk/react-ui";
import { useQueryState } from "nuqs";
import { useThreads } from "./Thread";
import { toast } from "sonner";
import { getUserId, getTodayDateString } from "@/lib/user";
import { createClient } from "./client";

export type StateType = { messages: Message[]; ui?: UIMessage[] };

const useTypedStream = useStream<
  StateType,
  {
    UpdateType: {
      messages?: Message[] | Message | string;
      ui?: (UIMessage | RemoveUIMessage)[] | UIMessage | RemoveUIMessage;
      context?: Record<string, unknown>;
    };
    CustomEventType: UIMessage | RemoveUIMessage;
  }
>;

type StreamContextType = ReturnType<typeof useTypedStream>;
const StreamContext = createContext<StreamContextType | undefined>(undefined);

async function sleep(ms = 4000) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function checkGraphStatus(apiUrl: string): Promise<boolean> {
  try {
    const res = await fetch(`${apiUrl}/info`);
    return res.ok;
  } catch (e) {
    console.error(e);
    return false;
  }
}

/**
 * 查找或创建今天的 Thread。
 * 按 user_id + date metadata 搜索；不存在则新建。
 */
async function ensureTodayThread(
  apiUrl: string,
  userId: string,
  assistantId: string,
  sessionType: "coaching" | "onboarding" = "coaching",
): Promise<string | null> {
  const client = createClient(apiUrl, undefined, undefined);
  const today = getTodayDateString();

  try {
    const existing = await client.threads.search({
      metadata: { user_id: userId, date: today, session_type: sessionType },
      limit: 1,
    });

    if (existing.length > 0) {
      return existing[0].thread_id;
    }

    const thread = await client.threads.create({
      metadata: {
        user_id: userId,
        date: today,
        session_type: sessionType,
        graph_id: assistantId,
        segment_status: "active",
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
    });

    return thread.thread_id;
  } catch (e) {
    console.error("Failed to ensure today thread:", e);
    return null;
  }
}

/**
 * 创建 onboarding thread 并发送用户名字作为第一条消息。
 */
export async function startOnboardingThread(
  apiUrl: string,
  userId: string,
  assistantId: string,
): Promise<string | null> {
  return ensureTodayThread(apiUrl, userId, assistantId, "onboarding");
}

function resolveApiUrl(url: string): string {
  if (url.startsWith("/") && typeof window !== "undefined") {
    return `${window.location.origin}${url}`;
  }
  return url;
}

const StreamSession = ({
  children,
  apiUrl: rawApiUrl,
  assistantId,
}: {
  children: ReactNode;
  apiUrl: string;
  assistantId: string;
}) => {
  const apiUrl = resolveApiUrl(rawApiUrl);
  const [threadId, setThreadId] = useQueryState("threadId");
  const { getThreads, setThreads } = useThreads();

  // 首次加载时，若无 threadId，尝试复用/创建今日 Thread
  const ensureInFlight = useRef(false);
  useEffect(() => {
    if (threadId || ensureInFlight.current) return;
    const userId = getUserId();
    if (!userId) return;

    ensureInFlight.current = true;
    ensureTodayThread(apiUrl, userId, assistantId)
      .then((id) => {
        if (id) setThreadId(id);
      })
      .finally(() => {
        ensureInFlight.current = false;
      });
  }, [threadId, apiUrl, assistantId, setThreadId]);

  const streamValue = useTypedStream({
    apiUrl,
    assistantId,
    threadId: threadId ?? null,
    fetchStateHistory: true,
    onCustomEvent: (event, options) => {
      if (isUIMessage(event) || isRemoveUIMessage(event)) {
        options.mutate((prev) => {
          const ui = uiMessageReducer(prev.ui ?? [], event);
          return { ...prev, ui };
        });
      }
    },
    onThreadId: (id) => {
      setThreadId(id);
      sleep().then(() => getThreads().then(setThreads).catch(console.error));
    },
  });

  useEffect(() => {
    checkGraphStatus(apiUrl).then((ok) => {
      if (!ok) {
        toast.error("Failed to connect to LangGraph server", {
          description: () => (
            <p>
              Please ensure your graph is running at <code>{apiUrl}</code>.
            </p>
          ),
          duration: 10000,
          richColors: true,
          closeButton: true,
        });
      }
    });
  }, [apiUrl]);

  return (
    <StreamContext.Provider value={streamValue}>
      {children}
    </StreamContext.Provider>
  );
};

export const StreamProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const assistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;

  if (!apiUrl || !assistantId) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-[#1A1816]/60">
          Missing NEXT_PUBLIC_API_URL or NEXT_PUBLIC_ASSISTANT_ID
        </p>
      </div>
    );
  }

  return (
    <StreamSession apiUrl={apiUrl} assistantId={assistantId}>
      {children}
    </StreamSession>
  );
};

export const useStreamContext = (): StreamContextType => {
  const context = useContext(StreamContext);
  if (context === undefined) {
    throw new Error("useStreamContext must be used within a StreamProvider");
  }
  return context;
};

export default StreamContext;
