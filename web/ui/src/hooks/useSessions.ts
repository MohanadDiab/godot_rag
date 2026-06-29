import { useCallback, useEffect, useState } from "react";
import type { ChatMessage, ChatSession, SessionsState } from "../types";

const SESSIONS_KEY = "godot_rag_sessions";
const ACTIVE_KEY = "godot_rag_active_session";

function newId(): string {
  return crypto.randomUUID();
}

function sessionTitle(messages: ChatMessage[]): string {
  const first = messages.find((m) => m.role === "user");
  if (!first) return "New chat";
  const text = first.content.trim();
  return text.length > 48 ? `${text.slice(0, 48)}…` : text;
}

function loadState(): SessionsState {
  try {
    const raw = localStorage.getItem(SESSIONS_KEY);
    const active = localStorage.getItem(ACTIVE_KEY);
    if (raw) {
      const sessions = JSON.parse(raw) as ChatSession[];
      return { sessions, activeSessionId: active };
    }
  } catch {
    // ignore
  }
  return { sessions: [], activeSessionId: null };
}

function persistState(state: SessionsState): void {
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(state.sessions));
  if (state.activeSessionId) {
    localStorage.setItem(ACTIVE_KEY, state.activeSessionId);
  } else {
    localStorage.removeItem(ACTIVE_KEY);
  }
}

export function useSessions() {
  const [state, setState] = useState<SessionsState>(loadState);

  useEffect(() => {
    persistState(state);
  }, [state]);

  const activeSession =
    state.sessions.find((s) => s.id === state.activeSessionId) ?? null;

  const createSession = useCallback(() => {
    const now = new Date().toISOString();
    const session: ChatSession = {
      id: newId(),
      title: "New chat",
      createdAt: now,
      updatedAt: now,
      messages: [],
    };
    setState((prev) => ({
      sessions: [session, ...prev.sessions],
      activeSessionId: session.id,
    }));
    return session.id;
  }, []);

  const selectSession = useCallback((id: string) => {
    setState((prev) => ({ ...prev, activeSessionId: id }));
  }, []);

  const deleteSession = useCallback((id: string) => {
    setState((prev) => {
      const sessions = prev.sessions.filter((s) => s.id !== id);
      const activeSessionId =
        prev.activeSessionId === id ? (sessions[0]?.id ?? null) : prev.activeSessionId;
      return { sessions, activeSessionId };
    });
  }, []);

  const updateSessionMessages = useCallback(
    (sessionId: string, messages: ChatMessage[]) => {
      const now = new Date().toISOString();
      setState((prev) => ({
        ...prev,
        sessions: prev.sessions.map((s) =>
          s.id === sessionId
            ? {
                ...s,
                messages,
                title: sessionTitle(messages),
                updatedAt: now,
              }
            : s,
        ),
      }));
    },
    [],
  );

  const ensureActiveSession = useCallback(() => {
    if (activeSession) return activeSession.id;
    return createSession();
  }, [activeSession, createSession]);

  return {
    sessions: state.sessions,
    activeSession,
    activeSessionId: state.activeSessionId,
    createSession,
    selectSession,
    deleteSession,
    updateSessionMessages,
    ensureActiveSession,
  };
}
