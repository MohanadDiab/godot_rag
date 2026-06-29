import { useCallback, useEffect, useState } from "react";
import { AlertDialog } from "./components/AlertDialog";
import { ChatPanel } from "./components/ChatPanel";
import { Sidebar } from "./components/Sidebar";
import {
  loadSettings,
  resolveModel,
  saveSettings,
  TopBar,
} from "./components/TopBar";
import { useChat } from "./hooks/useChat";
import { useSessions } from "./hooks/useSessions";
import type { ChatMessage } from "./types";
import "./App.css";

export default function App() {
  const settings = loadSettings();
  const [apiKey, setApiKey] = useState(settings.apiKey);
  const [model, setModel] = useState(settings.model);
  const [customModel, setCustomModel] = useState(settings.customModel);
  const [apiKeyAlert, setApiKeyAlert] = useState(false);

  const {
    sessions,
    activeSession,
    activeSessionId,
    createSession,
    selectSession,
    deleteSession,
    updateSessionMessages,
    ensureActiveSession,
  } = useSessions();

  useEffect(() => {
    if (sessions.length === 0) {
      createSession();
    }
  }, [sessions.length, createSession]);

  useEffect(() => {
    saveSettings(apiKey, model, customModel);
  }, [apiKey, model, customModel]);

  const resolvedModel = resolveModel(model, customModel);

  const handleMessagesUpdate = useCallback(
    (messages: ChatMessage[]) => {
      const sessionId = ensureActiveSession();
      updateSessionMessages(sessionId, messages);
    },
    [ensureActiveSession, updateSessionMessages],
  );

  const { sendMessage, isStreaming, phase, streamStartedAt, embeddingLoad } = useChat(
    apiKey,
    resolvedModel,
    handleMessagesUpdate,
  );

  const handleSend = async (text: string): Promise<boolean> => {
    if (!apiKey.trim()) {
      setApiKeyAlert(true);
      return false;
    }
    const sessionId = ensureActiveSession();
    const history = activeSession?.id === sessionId ? activeSession.messages : [];
    return sendMessage(history, text);
  };

  const handleNewChat = () => {
    createSession();
  };

  return (
    <div className="app">
      {apiKeyAlert && (
        <AlertDialog
          message="Enter your OpenAI API key in the top bar to send messages. The key is stored only in your browser."
          onClose={() => setApiKeyAlert(false)}
        />
      )}
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelect={selectSession}
        onDelete={deleteSession}
        onNewChat={handleNewChat}
      />
      <main className="main">
        <TopBar
          apiKey={apiKey}
          model={model}
          customModel={customModel}
          onApiKeyChange={setApiKey}
          onModelChange={setModel}
          onCustomModelChange={setCustomModel}
          onNewChat={handleNewChat}
        />
        <ChatPanel
          messages={activeSession?.messages ?? []}
          isStreaming={isStreaming}
          phase={phase}
          streamStartedAt={streamStartedAt}
          embeddingLoad={embeddingLoad}
          onSend={handleSend}
        />
      </main>
    </div>
  );
}
