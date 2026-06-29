import type { ChatMessage, ModelInfo, StreamEvent } from "./types";

export async function fetchModels(): Promise<ModelInfo[]> {
  const res = await fetch("/api/models");
  if (!res.ok) throw new Error("Failed to load models");
  const data = await res.json();
  return data.models;
}

export async function streamChat(
  messages: ChatMessage[],
  model: string,
  apiKey: string,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, model, api_key: apiKey }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data: ")) continue;
      try {
        const event = JSON.parse(line.slice(6)) as StreamEvent;
        onEvent(event);
      } catch {
        // ignore malformed chunks
      }
    }
  }
}
