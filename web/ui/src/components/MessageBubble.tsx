import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../types";
import { formatResponseTime } from "./AgentActivity";
import { markdownComponents } from "./CodeBlock";

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

function MessageBubbleInner({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`message ${isUser ? "user" : "assistant"}`}>
      <div className="message-role">{isUser ? "You" : "Godot RAG"}</div>
      <div className="message-body">
        {isUser ? (
          <p className="user-text">{message.content}</p>
        ) : (
          <>
            {message.content ? (
              <ReactMarkdown
                key={isStreaming ? "streaming" : "done"}
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {message.content}
              </ReactMarkdown>
            ) : null}
            {isStreaming && <span className="cursor-blink">▍</span>}
          </>
        )}
      </div>
      {!isUser && message.elapsedSeconds !== undefined && !isStreaming && (
        <div className="message-meta">{formatResponseTime(message.elapsedSeconds)}</div>
      )}
    </div>
  );
}

export const MessageBubble = memo(MessageBubbleInner);
