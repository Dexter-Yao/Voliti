// ABOUTME: Stream provider，封装 LangGraph useStream hook
// ABOUTME: 预创建或复用每日 Thread，并通过受信任代理边界补全真实用户身份

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
import { ThreadContext } from "./Thread";
import { toast } from "sonner";
import { ensureTodayThread } from "@/lib/thread-bootstrap";

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
  autoEnsureThread = true,
  onNewThread,
}: {
  children: ReactNode;
  apiUrl: string;
  assistantId: string;
  autoEnsureThread?: boolean;
  onNewThread?: () => void;
}) => {
  const apiUrl = resolveApiUrl(rawApiUrl);
  const [threadId, setThreadId] = useQueryState("threadId");
  const threadCtx = useContext(ThreadContext);

  // 首次加载时，若无 threadId，尝试复用/创建今日 Thread
  const ensureInFlight = useRef(false);
  useEffect(() => {
    if (!autoEnsureThread) return;
    if (threadId || ensureInFlight.current) return;

    ensureInFlight.current = true;
    ensureTodayThread(apiUrl, assistantId)
      .then((result) => {
        if (result) {
          setThreadId(result.threadId);
          if (result.isNew) onNewThread?.();
        }
      })
      .finally(() => {
        ensureInFlight.current = false;
      });
  }, [threadId, apiUrl, assistantId, autoEnsureThread, setThreadId]); // eslint-disable-line react-hooks/exhaustive-deps

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
      if (threadCtx) {
        sleep().then(() => threadCtx.getThreads().then(threadCtx.setThreads).catch(console.error));
      }
    },
  });

  useEffect(() => {
    checkGraphStatus(apiUrl).then((ok) => {
      if (!ok) {
        toast.error("Failed to connect to LangGraph server", {
          description: () => <p>当前无法连接教练服务，请稍后重试。</p>,
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

export const StreamProvider: React.FC<{
  children: ReactNode;
  autoEnsureThread?: boolean;
  onNewThread?: () => void;
}> = ({ children, autoEnsureThread = true, onNewThread }) => {
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
    <StreamSession
      apiUrl={apiUrl}
      assistantId={assistantId}
      autoEnsureThread={autoEnsureThread}
      onNewThread={onNewThread}
    >
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
