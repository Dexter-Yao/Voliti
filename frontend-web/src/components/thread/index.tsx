// ABOUTME: 主线程视图，三栏可拖拽布局（历史 | 对话 | Mirror/Artifact）
// ABOUTME: 使用 react-resizable-panels v4 实现可折叠可拖拽面板

import { v4 as uuidv4 } from "uuid";
import { ReactNode, useCallback, useEffect, useMemo, useRef } from "react";
import { cn } from "@/lib/utils";
import { useStreamContext } from "@/providers/Stream";
import { useState, FormEvent } from "react";
import { Button } from "../ui/button";
import { Checkpoint, Message } from "@langchain/langgraph-sdk";
import { AssistantMessage, AssistantMessageLoading } from "./messages/ai";
import { HumanMessage } from "./messages/human";
import {
  DO_NOT_RENDER_ID_PREFIX,
  ensureToolCallsHaveResponses,
} from "@/lib/ensure-tool-responses";
import { TooltipIconButton } from "./tooltip-icon-button";
import {
  ArrowDown,
  ArrowUp,
  LoaderCircle,
  Mic,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Settings,
  Square,
  XIcon,
} from "lucide-react";
import { useQueryState } from "nuqs";
import { StickToBottom, useStickToBottomContext } from "use-stick-to-bottom";
import ThreadHistory from "./history";
import { toast } from "sonner";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import {
  useArtifactOpen,
  ArtifactContent,
  ArtifactTitle,
  useArtifactContext,
} from "./artifact";
import { Group, Panel, Separator, usePanelRef } from "react-resizable-panels";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "../ui/sheet";
import { MirrorPanel } from "../mirror/MirrorPanel";
import { SettingsDrawer } from "../settings/SettingsDrawer";
import {
  isThreadSealed,
  SESSION_TYPE_COACHING,
  type SessionType,
} from "@/lib/thread-utils";
import { useThreads } from "@/providers/Thread";
import { buildSubmitConfig } from "@/lib/stream-config";
import {
  applyVoiceTranscriptionToComposerDraft,
  buildVoiceMessageAdditionalKwargs,
  createEmptyComposerDraft,
  updateComposerDraftText,
  type ComposerDraft,
  type VoiceTranscriptionResult,
} from "@/lib/voice";
import { useVoiceInput } from "@/hooks/use-voice-input";
import { fetchCoachContext, type CoachContextData } from "@/lib/store-sync";
import { CoachContextSummary } from "@/components/coach/CoachContextSummary";

function StickyToBottomContent(props: {
  content: ReactNode;
  footer?: ReactNode;
  className?: string;
  contentClassName?: string;
}) {
  const context = useStickToBottomContext();
  return (
    <div
      ref={context.scrollRef}
      style={{ width: "100%", height: "100%" }}
      className={props.className}
    >
      <div
        ref={context.contentRef}
        className={props.contentClassName}
      >
        {props.content}
      </div>

      {props.footer}
    </div>
  );
}

function ScrollToBottom(props: { className?: string }) {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext();

  if (isAtBottom) return null;
  return (
    <Button
      variant="outline"
      className={props.className}
      onClick={() => scrollToBottom()}
    >
      <ArrowDown className="h-4 w-4" />
      <span>滚动到底部</span>
    </Button>
  );
}

export function Thread({
  initialMessage,
  onInitialMessageSent,
}: {
  initialMessage?: string | null;
  onInitialMessageSent?: () => void;
} = {}) {
  const [artifactContext] = useArtifactContext();
  const [artifactOpen, closeArtifact] = useArtifactOpen();

  const [threadId] = useQueryState("threadId");
  const { threads } = useThreads();
  const isSealed = useMemo(() => {
    if (!threadId) return false;
    const thread = threads.find((t) => t.thread_id === threadId);
    return thread ? isThreadSealed(thread) : false;
  }, [threadId, threads]);
  const sessionType = useMemo(() => {
    if (!threadId) return SESSION_TYPE_COACHING;
    const thread = threads.find((t) => t.thread_id === threadId);
    const meta = thread?.metadata as Record<string, unknown> | undefined;
    return (meta?.session_type as SessionType) ?? SESSION_TYPE_COACHING;
  }, [threadId, threads]);
  const submitConfig = useMemo(
    () => buildSubmitConfig(sessionType),
    [sessionType],
  );
  const [composerDraft, setComposerDraft] = useState<ComposerDraft>(() =>
    createEmptyComposerDraft(),
  );
  const [coachContext, setCoachContext] = useState<CoachContextData | null>(null);
  const [firstTokenReceived, setFirstTokenReceived] = useState(false);
  const isMobile = useMediaQuery("(max-width: 767px)");
  const [mobileHistoryOpen, setMobileHistoryOpen] = useState(false);
  const [mobileMirrorOpen, setMobileMirrorOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Panel refs for programmatic collapse/expand
  const historyPanelRef = usePanelRef();
  const mirrorPanelRef = usePanelRef();
  const [historyCollapsed, setHistoryCollapsed] = useState(false);
  const [mirrorCollapsed, setMirrorCollapsed] = useState(true);

  const stream = useStreamContext();
  const messages = stream.messages;
  const isLoading = stream.isLoading;

  const lastError = useRef<string | undefined>(undefined);

  useEffect(() => {
    if (messages.length > 0) return;
    let cancelled = false;

    fetchCoachContext()
      .then((context) => {
        if (!cancelled) {
          setCoachContext(context);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCoachContext(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [messages.length, threadId]);

  // Sync collapsed state from panel resize events
  const syncCollapsedState = useCallback(() => {
    if (historyPanelRef.current) {
      setHistoryCollapsed(historyPanelRef.current.isCollapsed());
    }
    if (mirrorPanelRef.current) {
      setMirrorCollapsed(mirrorPanelRef.current.isCollapsed());
    }
  }, [historyPanelRef, mirrorPanelRef]);

  // Expand mirror panel when artifact opens
  useEffect(() => {
    if (artifactOpen && mirrorPanelRef.current) {
      mirrorPanelRef.current.resize("22%");
      setMirrorCollapsed(false);
    }
  }, [artifactOpen, mirrorPanelRef]);

  // Mirror 默认折叠（无数据时不占空间）
  useEffect(() => {
    mirrorPanelRef.current?.collapse();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!stream.error) {
      lastError.current = undefined;
      return;
    }
    try {
      const message = (stream.error as any).message;
      if (!message || lastError.current === message) return;
      lastError.current = message;
      toast.error("发生错误，请重试", {
        description: (
          <p>
            <strong>Error:</strong> <code>{message}</code>
          </p>
        ),
        richColors: true,
        closeButton: true,
      });
    } catch {
      // no-op
    }
  }, [stream.error]);

  // Auto-send initial message (e.g. [daily_checkin] trigger for coaching)
  const initialSent = useRef(false);
  useEffect(() => {
    if (!initialMessage || initialSent.current || isLoading) return;
    if (!threadId) return;
    initialSent.current = true;

    const isSystemTrigger = initialMessage.startsWith("[daily_");
    const msg: Message = {
      id: isSystemTrigger ? `${DO_NOT_RENDER_ID_PREFIX}${uuidv4()}` : uuidv4(),
      type: "human",
      content: [{ type: "text", text: initialMessage }] as Message["content"],
    };
    stream.submit(
      { messages: [msg] },
      {
        config: submitConfig,
        streamMode: ["values"],
        streamSubgraphs: true,
        streamResumable: true,
      },
    );
    onInitialMessageSent?.();
  }, [initialMessage, threadId, isLoading]); // eslint-disable-line react-hooks/exhaustive-deps

  const prevMessageLength = useRef(0);
  useEffect(() => {
    if (
      messages.length !== prevMessageLength.current &&
      messages?.length &&
      messages[messages.length - 1].type === "ai"
    ) {
      setFirstTokenReceived(true);
    }
    prevMessageLength.current = messages.length;
  }, [messages]);

  const voiceInput = useVoiceInput({
    disabled: isLoading || isSealed,
    onDraftReady: useCallback((draft: VoiceTranscriptionResult) => {
      setComposerDraft((previous) =>
        applyVoiceTranscriptionToComposerDraft(previous, draft),
      );
    }, []),
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (composerDraft.text.trim().length === 0 || isLoading || isSealed) return;
    setFirstTokenReceived(false);

    const voiceAdditionalKwargs = composerDraft.voiceMetadata
      ? buildVoiceMessageAdditionalKwargs(composerDraft.voiceMetadata)
      : undefined;

    const newHumanMessage: Message = {
      id: uuidv4(),
      type: "human",
      content: [
        { type: "text", text: composerDraft.text },
      ] as Message["content"],
      additional_kwargs: voiceAdditionalKwargs,
    };

    const toolMessages = ensureToolCallsHaveResponses(stream.messages);
    const context =
      Object.keys(artifactContext).length > 0 ? artifactContext : undefined;

    stream.submit(
      { messages: [...toolMessages, newHumanMessage], context },
      {
        config: submitConfig,
        streamMode: ["values"],
        streamSubgraphs: true,
        streamResumable: true,
        optimisticValues: (prev) => ({
          ...prev,
          context,
          messages: [
            ...(prev.messages ?? []),
            ...toolMessages,
            newHumanMessage,
          ],
        }),
      },
    );

    setComposerDraft(createEmptyComposerDraft());
  };

  const handleRegenerate = (
    parentCheckpoint: Checkpoint | null | undefined,
  ) => {
    if (isSealed) return;
    prevMessageLength.current = prevMessageLength.current - 1;
    setFirstTokenReceived(false);
    stream.submit(undefined, {
      config: submitConfig,
      checkpoint: parentCheckpoint,
      streamMode: ["values"],
      streamSubgraphs: true,
      streamResumable: true,
    });
  };

  const chatStarted = messages.length > 0;
  const hasNoAIOrToolMessages = !messages.find(
    (m) => m.type === "ai" || m.type === "tool",
  );

  const toggleHistory = () => {
    if (isMobile) {
      setMobileHistoryOpen((o) => !o);
    } else {
      const panel = historyPanelRef.current;
      if (!panel) return;
      if (panel.isCollapsed()) {
        panel.resize("18%");
      } else {
        panel.collapse();
      }
    }
  };

  const toggleMirror = () => {
    if (isMobile) {
      setMobileMirrorOpen((o) => !o);
      return;
    }
    const panel = mirrorPanelRef.current;
    if (!panel) return;
    if (panel.isCollapsed()) {
      panel.resize("22%");
    } else {
      panel.collapse();
    }
  };

  // Chat header
  const chatHeader = (
    <div className="relative z-10 flex items-center justify-between gap-3 border-b border-[#1A1816]/5 p-2">
      <div className="flex items-center gap-2">
        <TooltipIconButton
          tooltip={historyCollapsed || isMobile ? "展开历史" : "收起历史"}
          variant="ghost"
          onClick={toggleHistory}
        >
          {historyCollapsed || isMobile ? (
            <PanelLeftOpen className="size-5" />
          ) : (
            <PanelLeftClose className="size-5" />
          )}
        </TooltipIconButton>

        <span className="text-xl font-semibold tracking-tight">Voliti</span>
      </div>

      <div className="flex items-center gap-2">
        <TooltipIconButton
          tooltip={mirrorCollapsed ? "展开镜像" : "收起镜像"}
          variant="ghost"
          onClick={toggleMirror}
        >
          {mirrorCollapsed ? (
            <PanelRightOpen className="size-5" />
          ) : (
            <PanelRightClose className="size-5" />
          )}
        </TooltipIconButton>
        <TooltipIconButton
          tooltip="设置"
          variant="ghost"
          onClick={() => setSettingsOpen(true)}
        >
          <Settings className="size-5" />
        </TooltipIconButton>
      </div>
    </div>
  );

  // Chat content (messages + input)
  const chatContent = (
    <StickToBottom className="relative flex-1 overflow-hidden">
      <StickyToBottomContent
        className={cn(
          "absolute inset-0 overflow-y-scroll px-4 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-[#1A1816]/15 [&::-webkit-scrollbar-track]:bg-transparent",
          !chatStarted && "mt-[25vh] flex flex-col items-stretch",
          chatStarted && "grid grid-rows-[1fr_auto]",
        )}
        contentClassName="pt-8 pb-16 max-w-3xl mx-auto flex flex-col gap-4 w-full"
        content={
          <>
            {(() => {
              const visible = messages.filter((m) => {
                if (m.id?.startsWith(DO_NOT_RENDER_ID_PREFIX)) return false;
                if (m.type === "tool") return false;
                if (
                  m.type === "ai" &&
                  "tool_calls" in m &&
                  m.tool_calls?.length
                ) {
                  const text =
                    typeof m.content === "string"
                      ? m.content
                      : (m.content ?? [])
                          .filter((c: any) => c.type === "text")
                          .map((c: any) => c.text)
                          .join("");
                  if (!text.trim()) return false;
                }
                return true;
              });
              return visible.map((message, index) =>
                message.type === "human" ? (
                  <HumanMessage
                    key={message.id || `${message.type}-${index}`}
                    message={message}
                    isLoading={isLoading}
                  />
                ) : (
                  <AssistantMessage
                    key={message.id || `${message.type}-${index}`}
                    message={message}
                    isLoading={isLoading}
                    handleRegenerate={handleRegenerate}
                  />
                ),
              );
            })()}
            {hasNoAIOrToolMessages && !!stream.interrupt && (
              <AssistantMessage
                key="interrupt-msg"
                message={undefined}
                isLoading={isLoading}
                handleRegenerate={handleRegenerate}
              />
            )}
            {isLoading && !firstTokenReceived && (
              <AssistantMessageLoading
                toolName={
                  messages.length > 0
                    ? (() => {
                        const last = messages[messages.length - 1];
                        const calls =
                          last?.type === "ai"
                            ? (last as any).tool_calls
                            : undefined;
                        return calls?.length
                          ? calls[calls.length - 1].name
                          : undefined;
                      })()
                    : undefined
                }
              />
            )}
          </>
        }
        footer={
          <div className="sticky bottom-0 flex flex-col items-center gap-4 bg-[#F4F0E8]">
            {/* Empty state welcome */}
            {!chatStarted && (
              <div className="flex w-full flex-col items-center gap-4 pb-4">
                <h1 className="font-serif-coach text-2xl text-[#1A1816]">
                  Voliti
                </h1>
                <p className="text-sm text-[#1A1816]/40">
                  {coachContext ? "你现在最值得先守住的是这些。" : "今天想聊什么？"}
                </p>
                {coachContext && (
                  <div className="w-full">
                    <CoachContextSummary context={coachContext} compact />
                  </div>
                )}
              </div>
            )}

            <ScrollToBottom className="animate-in fade-in-0 zoom-in-95 absolute bottom-full left-1/2 mb-4 -translate-x-1/2" />

            {/* Suggested reply pills */}
            {/* Input area */}
            <div className="relative z-10 mx-auto mb-6 w-full max-w-3xl">
              {(() => {
                const hasVoiceMetadata = Boolean(composerDraft.voiceMetadata);
                const showVoiceStatus =
                  voiceInput.isRecording ||
                  voiceInput.isTranscribing ||
                  voiceInput.hasError ||
                  hasVoiceMetadata;
                const voiceStatusLabel = voiceInput.isRecording
                  ? "正在录音"
                  : voiceInput.isTranscribing
                    ? "正在转写"
                    : voiceInput.hasError
                      ? "转写失败"
                      : hasVoiceMetadata
                        ? composerDraft.voiceMetadata?.confirmed
                          ? "语音待发送"
                          : "语音已编辑"
                        : null;

                return (
                  <form
                    onSubmit={handleSubmit}
                    className="flex items-end gap-2 rounded-[4px] border border-[#1A1816]/10 bg-transparent px-4 py-3"
                  >
                    <textarea
                      value={composerDraft.text}
                      onChange={(e) => {
                        setComposerDraft((previous) =>
                          updateComposerDraftText(previous, e.target.value),
                        );
                      }}
                      onKeyDown={(e) => {
                        if (
                          e.key === "Enter" &&
                          !e.shiftKey &&
                          !e.metaKey &&
                          !e.nativeEvent.isComposing
                        ) {
                          e.preventDefault();
                          const el = e.target as HTMLElement | undefined;
                          const form = el?.closest("form");
                          form?.requestSubmit();
                        }
                      }}
                      disabled={isSealed}
                      placeholder={isSealed ? "本次对话已结束" : "输入消息…"}
                      rows={1}
                      className="field-sizing-content max-h-32 flex-1 resize-none border-none bg-transparent text-sm text-[#1A1816] shadow-none ring-0 outline-none placeholder:text-[#1A1816]/30 focus:ring-0 focus:outline-none disabled:cursor-not-allowed disabled:opacity-40"
                    />

                    {showVoiceStatus && (
                      <div className="flex min-w-0 items-center gap-2 self-center">
                        <span className="truncate font-mono text-[11px] text-[#1A1816]/50">
                          {voiceStatusLabel}
                        </span>
                        {voiceInput.hasError ? (
                          <>
                            <button
                              type="button"
                              onClick={() =>
                                void voiceInput.retryTranscription()
                              }
                              className="text-[11px] text-[#1A1816]/70 transition-colors hover:text-[#1A1816]"
                            >
                              重试
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                voiceInput.discardLastRecording();
                              }}
                              className="text-[11px] text-[#1A1816]/45 transition-colors hover:text-[#1A1816]/70"
                            >
                              丢弃
                            </button>
                          </>
                        ) : composerDraft.voiceMetadata ? (
                          <button
                            type="button"
                            onClick={() => {
                              setComposerDraft((previous) => ({
                                ...previous,
                                voiceMetadata: null,
                              }));
                              voiceInput.clearError();
                            }}
                            className="text-[11px] text-[#1A1816]/45 transition-colors hover:text-[#1A1816]/70"
                          >
                            取消语音
                          </button>
                        ) : null}
                      </div>
                    )}

                    <button
                      type="button"
                      disabled={
                        isLoading || isSealed || voiceInput.isTranscribing
                      }
                      onPointerDown={(event) => {
                        event.preventDefault();
                        void voiceInput.beginRecording();
                      }}
                      onPointerUp={() => {
                        voiceInput.stopRecording();
                      }}
                      onPointerCancel={() => {
                        voiceInput.stopRecording();
                      }}
                      className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-none border border-[#1A1816]/10 text-[#1A1816] transition-colors disabled:cursor-not-allowed disabled:opacity-20"
                      aria-label={
                        voiceInput.isRecording
                          ? "正在录音，松开发起转写"
                          : "按住开始录音"
                      }
                    >
                      {voiceInput.isTranscribing ? (
                        <LoaderCircle className="h-4 w-4 animate-spin" />
                      ) : voiceInput.isRecording ? (
                        <Square className="h-4 w-4 fill-current text-[#B04F35]" />
                      ) : (
                        <Mic className="h-4 w-4" />
                      )}
                    </button>

                    {stream.isLoading ? (
                      <button
                        type="button"
                        onClick={() => stream.stop()}
                        className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-none bg-[#1A1816] text-[#F4F0E8]"
                      >
                        <LoaderCircle className="h-4 w-4 animate-spin" />
                      </button>
                    ) : (
                      <button
                        type="submit"
                        disabled={
                          isLoading ||
                          isSealed ||
                          voiceInput.isTranscribing ||
                          !composerDraft.text.trim()
                        }
                        className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-none bg-[#1A1816] text-[#F4F0E8] transition-opacity disabled:opacity-20"
                      >
                        <ArrowUp className="h-4 w-4" />
                      </button>
                    )}
                  </form>
                );
              })()}
            </div>
          </div>
        }
      />
    </StickToBottom>
  );

  // Mobile: Sheet overlay for history
  const mobileHistorySheet = (
    <Sheet
      open={mobileHistoryOpen}
      onOpenChange={setMobileHistoryOpen}
    >
      <SheetContent
        side="left"
        className="w-[300px] p-0"
      >
        <SheetHeader className="px-4 pt-4">
          <SheetTitle>历史记录</SheetTitle>
        </SheetHeader>
        <ThreadHistory onThreadSelect={() => setMobileHistoryOpen(false)} />
      </SheetContent>
    </Sheet>
  );

  // Mobile: Sheet overlay for mirror
  const mobileMirrorSheet = (
    <Sheet
      open={mobileMirrorOpen}
      onOpenChange={setMobileMirrorOpen}
    >
      <SheetContent
        side="right"
        className="w-[300px] p-0"
      >
        <SheetHeader className="px-4 pt-4">
          <SheetTitle>镜像</SheetTitle>
        </SheetHeader>
        <MirrorPanel />
      </SheetContent>
    </Sheet>
  );

  // Right panel content (Artifact / Mirror)
  const rightPanelContent = (
    <div className="flex h-full flex-col">
      {artifactOpen ? (
        <>
          <div className="grid grid-cols-[1fr_auto] border-b p-4">
            <ArtifactTitle className="truncate overflow-hidden" />
            <button
              onClick={closeArtifact}
              className="cursor-pointer"
            >
              <XIcon className="size-5" />
            </button>
          </div>
          <ArtifactContent className="relative flex-grow" />
        </>
      ) : (
        <MirrorPanel />
      )}
    </div>
  );

  // Mobile layout: single column, sheet for history
  if (isMobile) {
    return (
      <div className="flex h-screen w-full flex-col overflow-hidden">
        {chatHeader}
        {chatContent}
        {mobileHistorySheet}
        {mobileMirrorSheet}
        <SettingsDrawer
          open={settingsOpen}
          onOpenChange={setSettingsOpen}
        />
      </div>
    );
  }

  // Desktop layout: three resizable panels
  return (
    <div className="flex h-screen w-full overflow-hidden">
      <SettingsDrawer
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
      />
      <Group
        orientation="horizontal"
        id="voliti-layout"
        onLayoutChanged={syncCollapsedState}
      >
        {/* Left: History */}
        <Panel
          panelRef={historyPanelRef}
          id="history"
          collapsible
          collapsedSize="0%"
          minSize="15%"
          maxSize="25%"
          defaultSize="18%"
        >
          <div className="flex h-full flex-col overflow-hidden">
            <ThreadHistory />
          </div>
        </Panel>

        <Separator
          className={cn(
            "group relative transition-all",
            historyCollapsed ? "w-0" : "w-1 hover:w-1.5",
          )}
        >
          {!historyCollapsed && (
            <div className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-[#1A1816]/10 transition-colors group-hover:bg-[#B87333] group-active:bg-[#B87333]" />
          )}
        </Separator>

        {/* Center: Chat */}
        <Panel
          id="chat"
          minSize="35%"
        >
          <div className="flex h-full flex-col">
            {chatHeader}
            {chatContent}
          </div>
        </Panel>

        <Separator
          className={cn(
            "group relative transition-all",
            mirrorCollapsed ? "w-0" : "w-1 hover:w-1.5",
          )}
        >
          {!mirrorCollapsed && (
            <div className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-[#1A1816]/10 transition-colors group-hover:bg-[#B87333] group-active:bg-[#B87333]" />
          )}
        </Separator>

        {/* Right: Mirror / Artifact */}
        <Panel
          panelRef={mirrorPanelRef}
          id="mirror"
          collapsible
          collapsedSize="0%"
          minSize="15%"
          maxSize="30%"
          defaultSize="22%"
        >
          <div className="h-full overflow-hidden">{rightPanelContent}</div>
        </Panel>
      </Group>
    </div>
  );
}
