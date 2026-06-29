import { useCallback, useRef, useState } from "react";
import { streamChat } from "../api";
import type { AgentPhase, EmbeddingLoadState, ChatMessage } from "../types";

export function useChat(
  apiKey: string,
  model: string,
  onMessagesUpdate: (messages: ChatMessage[]) => void,
) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [phase, setPhase] = useState<AgentPhase | null>(null);
  const [streamStartedAt, setStreamStartedAt] = useState<number | null>(null);
  const [embeddingLoad, setEmbeddingLoad] = useState<EmbeddingLoadState | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const hasTokensRef = useRef(false);

  const sendMessage = useCallback(
    async (history: ChatMessage[], userText: string): Promise<boolean> => {
      if (!userText.trim() || isStreaming) return false;

      if (!apiKey.trim()) {
        return false;
      }

      const userMessage: ChatMessage = { role: "user", content: userText.trim() };
      const withUser = [...history, userMessage];
      const assistantMessage: ChatMessage = { role: "assistant", content: "" };
      const draft = [...withUser, assistantMessage];

      onMessagesUpdate(draft);
      setIsStreaming(true);
      setPhase("starting");
      setStreamStartedAt(Date.now());
      setEmbeddingLoad(null);
      startTimeRef.current = Date.now();
      hasTokensRef.current = false;

      const controller = new AbortController();
      abortRef.current = controller;

      const thinkingTimer = window.setTimeout(() => {
        setPhase((current) => (current === "starting" ? "thinking" : current));
      }, 600);

      const finalizeAssistant = (content: string, elapsed?: number) => {
        const final: ChatMessage = {
          role: "assistant",
          content,
          ...(elapsed !== undefined ? { elapsedSeconds: elapsed } : {}),
        };
        onMessagesUpdate([...withUser, final]);
      };

      try {
        await streamChat(
          withUser,
          model,
          apiKey.trim(),
          (event) => {
            if (event.type === "embeddings_start") {
              setPhase("loading_embeddings");
              setEmbeddingLoad({ progress: 0, message: "Loading embedding model…" });
            } else if (event.type === "embeddings_progress") {
              setPhase("loading_embeddings");
              setEmbeddingLoad({
                progress: event.progress,
                message: event.message,
              });
            } else if (event.type === "embeddings_ready") {
              setEmbeddingLoad({ progress: 100, message: "Embedding model ready" });
              setPhase("starting");
            } else if (event.type === "token") {
              if (!hasTokensRef.current) {
                hasTokensRef.current = true;
                setPhase("writing");
              }
              assistantMessage.content += event.content;
              onMessagesUpdate([...withUser, { ...assistantMessage }]);
            } else if (event.type === "tool_start") {
              setPhase("retrieving");
            } else if (event.type === "tool_end") {
              if (!hasTokensRef.current) {
                setPhase("thinking");
              }
            } else if (event.type === "done") {
              assistantMessage.content = event.content || assistantMessage.content;
              const elapsed =
                startTimeRef.current !== null
                  ? (Date.now() - startTimeRef.current) / 1000
                  : undefined;
              finalizeAssistant(assistantMessage.content, elapsed);
            } else if (event.type === "error") {
              throw new Error(event.message);
            }
          },
          controller.signal,
        );

        if (!assistantMessage.content && startTimeRef.current !== null) {
          const elapsed = (Date.now() - startTimeRef.current) / 1000;
          finalizeAssistant(assistantMessage.content, elapsed);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Request failed";
        const content = assistantMessage.content || `Error: ${message}`;
        const elapsed =
          startTimeRef.current !== null
            ? (Date.now() - startTimeRef.current) / 1000
            : undefined;
        finalizeAssistant(content, elapsed);
      } finally {
        window.clearTimeout(thinkingTimer);
        setIsStreaming(false);
        setPhase(null);
        setStreamStartedAt(null);
        setEmbeddingLoad(null);
        startTimeRef.current = null;
        hasTokensRef.current = false;
        abortRef.current = null;
      }
      return true;
    },
    [apiKey, model, isStreaming, onMessagesUpdate],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { sendMessage, isStreaming, phase, streamStartedAt, embeddingLoad, stop };
}
