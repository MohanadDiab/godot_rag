import { memo, useEffect, useRef, useState } from "react";
import type { AgentPhase, ChatMessage, EmbeddingLoadState } from "../types";
import { AgentActivity } from "./AgentActivity";
import { MessageBubble } from "./MessageBubble";
import { useChatScroll } from "../hooks/useChatScroll";

const EXAMPLE_PROMPTS = [
  "How do I instance scenes and use PackedScene in Godot 4?",
  "How do I connect signals (e.g., Button pressed) in GDScript or C#?",
  "What's the best way to implement basic player movement in 2D or 3D?",
  "How do I set up UI with anchors and connect signals for UI widgets?",
  "How do animations and AnimationTree work in Godot 4?",
  "What does a typical Godot 4 project structure look like, and what are common starter patterns?",
] as const;

interface ChatPanelProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  phase: AgentPhase | null;
  streamStartedAt: number | null;
  embeddingLoad: EmbeddingLoadState | null;
  onSend: (text: string) => Promise<boolean>;
}

function ChatPanelInner({
  messages,
  isStreaming,
  phase,
  streamStartedAt,
  embeddingLoad,
  onSend,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const phaseScrollRef = useRef<string | null>(null);

  const lastMessage = messages[messages.length - 1];
  const streamingContentLength =
    isStreaming && lastMessage?.role === "assistant" ? lastMessage.content.length : 0;

  const { containerRef, pinToBottom } = useChatScroll(
    messages.length,
    streamingContentLength,
    isStreaming,
  );

  const hasAssistantContent =
    lastMessage?.role === "assistant" && Boolean(lastMessage.content);

  // Scroll once when activity phase changes (not on timer or progress ticks).
  useEffect(() => {
    if (!isStreaming || !phase) return;
    if (phaseScrollRef.current === phase) return;
    phaseScrollRef.current = phase;
    pinToBottom();
  }, [phase, isStreaming, pinToBottom]);

  useEffect(() => {
    if (!isStreaming) {
      phaseScrollRef.current = null;
    }
  }, [isStreaming]);

  const trySend = async (text: string) => {
    if (!text.trim() || isStreaming) return;
    const sent = await onSend(text);
    if (sent) setInput("");
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    void trySend(input);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void trySend(input);
    }
  };

  return (
    <div className="chat-panel">
      <div className="messages" ref={containerRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            <h3>Ask about Godot 4.x</h3>
            <p>
              Questions are answered using official docs and demo projects.
              Add your OpenAI key above to get started.
            </p>
            <div className="example-prompts">
              <p className="example-prompts-label">Try an example</p>
              <div className="example-prompts-list">
                {EXAMPLE_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="example-prompt"
                    disabled={isStreaming}
                    onClick={() => void trySend(prompt)}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            isStreaming={
              isStreaming && i === messages.length - 1 && msg.role === "assistant"
            }
          />
        ))}
        {isStreaming && phase && streamStartedAt !== null && (
          <AgentActivity
            phase={phase}
            startedAt={streamStartedAt}
            compact={phase === "writing" && hasAssistantContent}
            embeddingLoad={phase === "loading_embeddings" ? embeddingLoad : null}
          />
        )}
      </div>
      <form className="composer" onSubmit={submit}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask a Godot question… (Enter to send, Shift+Enter for newline)"
          rows={3}
          disabled={isStreaming}
        />
        <button type="submit" className="btn primary" disabled={isStreaming || !input.trim()}>
          {isStreaming ? "Sending…" : "Send"}
        </button>
      </form>
    </div>
  );
}

export const ChatPanel = memo(ChatPanelInner);
