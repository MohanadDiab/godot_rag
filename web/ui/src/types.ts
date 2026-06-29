export type ChatRole = "user" | "assistant";

export type AgentPhase =
  | "loading_embeddings"
  | "starting"
  | "retrieving"
  | "thinking"
  | "writing";

export interface EmbeddingLoadState {
  progress: number;
  message: string;
}

export interface ChatMessage {
  role: ChatRole;
  content: string;
  /** Wall-clock seconds for the assistant reply, set when the stream completes. */
  elapsedSeconds?: number;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

export interface SessionsState {
  sessions: ChatSession[];
  activeSessionId: string | null;
}

export type StreamEvent =
  | { type: "embeddings_start"; model: string }
  | { type: "embeddings_progress"; progress: number; message: string }
  | { type: "embeddings_ready" }
  | { type: "token"; content: string }
  | { type: "tool_start"; tool: string }
  | { type: "tool_end"; tool: string }
  | { type: "done"; content: string }
  | { type: "error"; message: string };

export interface ModelInfo {
  id: string;
  label: string;
}
