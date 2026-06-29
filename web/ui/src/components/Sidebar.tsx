import type { ChatSession } from "../types";

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onNewChat: () => void;
}

export function Sidebar({
  sessions,
  activeSessionId,
  onSelect,
  onDelete,
  onNewChat,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>History</h2>
        <button type="button" className="btn small" onClick={onNewChat}>
          +
        </button>
      </div>
      <ul className="session-list">
        {sessions.length === 0 && (
          <li className="session-empty">No chats yet</li>
        )}
        {sessions.map((session) => (
          <li key={session.id}>
            <button
              type="button"
              className={`session-item ${session.id === activeSessionId ? "active" : ""}`}
              onClick={() => onSelect(session.id)}
            >
              <span className="session-title">{session.title}</span>
            </button>
            <button
              type="button"
              className="session-delete"
              title="Delete chat"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(session.id);
              }}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
