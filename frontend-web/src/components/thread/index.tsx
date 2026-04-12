// ABOUTME: 主线程视图，三栏可拖拽布局（历史 | 对话 | Mirror/Artifact）
// ABOUTME: 使用 react-resizable-panels v4 实现可折叠可拖拽面板

import { v4 as uuidv4 } from "uuid";
import { ReactNode, useCallback, useEffect, useRef } from "react";
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
  LoaderCircle,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Settings,
  SquarePen,
  XIcon,
  Plus,
} from "lucide-react";
import { useQueryState, parseAsBoolean } from "nuqs";
import { StickToBottom, useStickToBottomContext } from "use-stick-to-bottom";
import ThreadHistory from "./history";
import { toast } from "sonner";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import { useFileUpload } from "@/hooks/use-file-upload";
import { ContentBlocksPreview } from "./ContentBlocksPreview";
import {
  useArtifactOpen,
  ArtifactContent,
  ArtifactTitle,
  useArtifactContext,
} from "./artifact";
import {
  Group,
  Panel,
  Separator,
  usePanelRef,
  type PanelImperativeHandle,
} from "react-resizable-panels";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "../ui/sheet";
import { MirrorPanel } from "../mirror/MirrorPanel";
import { SettingsDrawer } from "../settings/SettingsDrawer";

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
      <span>Scroll to bottom</span>
    </Button>
  );
}

export function Thread() {
  const [artifactContext, setArtifactContext] = useArtifactContext();
  const [artifactOpen, closeArtifact] = useArtifactOpen();

  const [threadId, _setThreadId] = useQueryState("threadId");
  const [hideToolCalls, setHideToolCalls] = useQueryState(
    "hideToolCalls",
    parseAsBoolean.withDefault(false),
  );
  const [input, setInput] = useState("");
  const {
    contentBlocks,
    setContentBlocks,
    handleFileUpload,
    dropRef,
    removeBlock,
    resetBlocks: _resetBlocks,
    dragOver,
    handlePaste,
  } = useFileUpload();
  const [firstTokenReceived, setFirstTokenReceived] = useState(false);
  const [suggestedReplies, setSuggestedReplies] = useState<string[]>([]);
  const isMobile = useMediaQuery("(max-width: 767px)");
  const [mobileHistoryOpen, setMobileHistoryOpen] = useState(false);
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

  const setThreadId = (id: string | null) => {
    _setThreadId(id);
    closeArtifact();
    setArtifactContext({});
  };

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
      mirrorPanelRef.current.expand();
      setMirrorCollapsed(false);
    }
  }, [artifactOpen, mirrorPanelRef]);

  useEffect(() => {
    if (!stream.error) {
      lastError.current = undefined;
      return;
    }
    try {
      const message = (stream.error as any).message;
      if (!message || lastError.current === message) return;
      lastError.current = message;
      toast.error("An error occurred. Please try again.", {
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

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if ((input.trim().length === 0 && contentBlocks.length === 0) || isLoading)
      return;
    setFirstTokenReceived(false);

    const newHumanMessage: Message = {
      id: uuidv4(),
      type: "human",
      content: [
        ...(input.trim().length > 0 ? [{ type: "text", text: input }] : []),
        ...contentBlocks,
      ] as Message["content"],
    };

    const toolMessages = ensureToolCallsHaveResponses(stream.messages);
    const context =
      Object.keys(artifactContext).length > 0 ? artifactContext : undefined;

    stream.submit(
      { messages: [...toolMessages, newHumanMessage], context },
      {
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

    setInput("");
    setContentBlocks([]);
  };

  const handleRegenerate = (
    parentCheckpoint: Checkpoint | null | undefined,
  ) => {
    prevMessageLength.current = prevMessageLength.current - 1;
    setFirstTokenReceived(false);
    stream.submit(undefined, {
      checkpoint: parentCheckpoint,
      streamMode: ["values"],
      streamSubgraphs: true,
      streamResumable: true,
    });
  };

  const chatStarted = !!threadId || !!messages.length;
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
        panel.expand();
      } else {
        panel.collapse();
      }
      // State will be synced via onResize
    }
  };

  const toggleMirror = () => {
    const panel = mirrorPanelRef.current;
    if (!panel) return;
    if (panel.isCollapsed()) {
      panel.expand();
    } else {
      panel.collapse();
    }
  };

  // Chat header
  const chatHeader = (
    <div className="relative z-10 flex items-center justify-between gap-3 border-b border-[#1A1816]/5 p-2">
      <div className="flex items-center gap-2">
        <TooltipIconButton
          tooltip={historyCollapsed || isMobile ? "Show history" : "Hide history"}
          variant="ghost"
          onClick={toggleHistory}
        >
          {historyCollapsed || isMobile ? (
            <PanelLeftOpen className="size-5" />
          ) : (
            <PanelLeftClose className="size-5" />
          )}
        </TooltipIconButton>

        {chatStarted && (
          <button
            className="flex cursor-pointer items-center gap-2"
            onClick={() => setThreadId(null)}
          >
            <span className="text-xl font-semibold tracking-tight">
              Voliti
            </span>
          </button>
        )}
      </div>

      <div className="flex items-center gap-2">
        {!isMobile && (
          <TooltipIconButton
            tooltip={mirrorCollapsed ? "Show mirror" : "Hide mirror"}
            variant="ghost"
            onClick={toggleMirror}
          >
            {mirrorCollapsed ? (
              <PanelRightOpen className="size-5" />
            ) : (
              <PanelRightClose className="size-5" />
            )}
          </TooltipIconButton>
        )}
        <TooltipIconButton
          tooltip="New thread"
          variant="ghost"
          onClick={() => setThreadId(null)}
        >
          <SquarePen className="size-5" />
        </TooltipIconButton>
        <TooltipIconButton
          tooltip="Settings"
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
            {messages
              .filter((m) => !m.id?.startsWith(DO_NOT_RENDER_ID_PREFIX))
              .map((message, index) =>
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
                    onSuggestedReplies={
                      index === messages.filter((m) => !m.id?.startsWith(DO_NOT_RENDER_ID_PREFIX)).length - 1
                        ? setSuggestedReplies
                        : undefined
                    }
                  />
                ),
              )}
            {hasNoAIOrToolMessages && !!stream.interrupt && (
              <AssistantMessage
                key="interrupt-msg"
                message={undefined}
                isLoading={isLoading}
                handleRegenerate={handleRegenerate}
              />
            )}
            {isLoading && !firstTokenReceived && <AssistantMessageLoading />}
          </>
        }
        footer={
          <div className="sticky bottom-0 flex flex-col items-center gap-8 bg-white">
            {!chatStarted && (
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-semibold tracking-tight">
                  Voliti
                </h1>
              </div>
            )}

            <ScrollToBottom className="animate-in fade-in-0 zoom-in-95 absolute bottom-full left-1/2 mb-4 -translate-x-1/2" />

            {/* Suggested reply pills */}
            {suggestedReplies.length > 0 && !isLoading && (
              <div className="mx-auto flex w-full max-w-3xl flex-wrap gap-2 px-1">
                {suggestedReplies.map((reply) => (
                  <button
                    key={reply}
                    onClick={() => {
                      setInput(reply);
                      setSuggestedReplies([]);
                    }}
                    className="rounded-pill border border-[#1A1816]/10 bg-white px-4 py-2 text-sm text-[#1A1816]/70 transition-colors hover:border-[#B87333] hover:text-[#1A1816]"
                  >
                    {reply}
                  </button>
                ))}
              </div>
            )}

            <div
              ref={dropRef}
              className={cn(
                "bg-muted relative z-10 mx-auto mb-8 w-full max-w-3xl rounded-2xl shadow-xs transition-all",
                dragOver
                  ? "border-primary border-2 border-dotted"
                  : "border border-solid",
              )}
            >
              <form
                onSubmit={handleSubmit}
                className="mx-auto grid max-w-3xl grid-rows-[1fr_auto] gap-2"
              >
                <ContentBlocksPreview
                  blocks={contentBlocks}
                  onRemove={removeBlock}
                />
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onPaste={handlePaste}
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
                  placeholder="Type your message..."
                  className="field-sizing-content resize-none border-none bg-transparent p-3.5 pb-0 shadow-none ring-0 outline-none focus:ring-0 focus:outline-none"
                />

                <div className="flex items-center gap-6 p-2 pt-4">
                  <div>
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="render-tool-calls"
                        checked={hideToolCalls ?? false}
                        onCheckedChange={setHideToolCalls}
                      />
                      <Label
                        htmlFor="render-tool-calls"
                        className="text-sm text-gray-600"
                      >
                        Hide Tool Calls
                      </Label>
                    </div>
                  </div>
                  <Label
                    htmlFor="file-input"
                    className="flex cursor-pointer items-center gap-2"
                  >
                    <Plus className="size-5 text-gray-600" />
                    <span className="text-sm text-gray-600">
                      Upload PDF or Image
                    </span>
                  </Label>
                  <input
                    id="file-input"
                    type="file"
                    onChange={handleFileUpload}
                    multiple
                    accept="image/jpeg,image/png,image/gif,image/webp,application/pdf"
                    className="hidden"
                  />
                  {stream.isLoading ? (
                    <Button
                      key="stop"
                      onClick={() => stream.stop()}
                      className="ml-auto"
                    >
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                      Cancel
                    </Button>
                  ) : (
                    <Button
                      type="submit"
                      className="ml-auto shadow-md transition-all"
                      disabled={
                        isLoading ||
                        (!input.trim() && contentBlocks.length === 0)
                      }
                    >
                      Send
                    </Button>
                  )}
                </div>
              </form>
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
      <SheetContent side="left" className="w-[300px] p-0">
        <SheetHeader className="px-4 pt-4">
          <SheetTitle>History</SheetTitle>
        </SheetHeader>
        <ThreadHistory onThreadSelect={() => setMobileHistoryOpen(false)} />
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
            <button onClick={closeArtifact} className="cursor-pointer">
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
        <SettingsDrawer open={settingsOpen} onOpenChange={setSettingsOpen} />
      </div>
    );
  }

  // Desktop layout: three resizable panels
  return (
    <div className="flex h-screen w-full overflow-hidden">
      <SettingsDrawer open={settingsOpen} onOpenChange={setSettingsOpen} />
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
          collapsedSize={0}
          minSize={15}
          maxSize={25}
          defaultSize={18}
        >
          <div className="flex h-full flex-col border-r border-[#1A1816]/5">
            <ThreadHistory />
          </div>
        </Panel>

        <Separator className="group relative w-1 transition-all hover:w-1.5">
          <div className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-[#1A1816]/10 transition-colors group-hover:bg-[#B87333] group-active:bg-[#B87333]" />
        </Separator>

        {/* Center: Chat */}
        <Panel
          id="chat"
          minSize={35}
        >
          <div className="flex h-full flex-col">
            {chatHeader}
            {chatContent}
          </div>
        </Panel>

        <Separator className="group relative w-1 transition-all hover:w-1.5">
          <div className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-[#1A1816]/10 transition-colors group-hover:bg-[#B87333] group-active:bg-[#B87333]" />
        </Separator>

        {/* Right: Mirror / Artifact */}
        <Panel
          panelRef={mirrorPanelRef}
          id="mirror"
          collapsible
          collapsedSize={0}
          minSize={15}
          maxSize={30}
          defaultSize={0}
        >
          <div className="h-full border-l border-[#1A1816]/5">
            {rightPanelContent}
          </div>
        </Panel>
      </Group>
    </div>
  );
}
