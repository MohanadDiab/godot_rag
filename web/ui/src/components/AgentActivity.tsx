import { useEffect, useState } from "react";
import type { AgentPhase, EmbeddingLoadState } from "../types";

const PHASE_LABELS: Record<AgentPhase, string> = {
  loading_embeddings: "Loading embedding model…",
  starting: "Starting…",
  retrieving: "Retrieving related docs…",
  thinking: "Thinking…",
  writing: "Writing answer…",
};

interface AgentActivityProps {
  phase: AgentPhase;
  startedAt: number | null;
  compact?: boolean;
  embeddingLoad?: EmbeddingLoadState | null;
}

function formatElapsed(seconds: number): string {
  return `${seconds.toFixed(2)}s`;
}

export function AgentActivity({
  phase,
  startedAt,
  compact = false,
  embeddingLoad = null,
}: AgentActivityProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (startedAt === null) {
      setElapsedSeconds(0);
      return;
    }

    const tick = () => setElapsedSeconds((Date.now() - startedAt) / 1000);
    tick();
    const id = window.setInterval(tick, 100);
    return () => window.clearInterval(id);
  }, [startedAt]);

  const label =
    phase === "loading_embeddings" && embeddingLoad?.message
      ? embeddingLoad.message
      : PHASE_LABELS[phase];

  return (
    <div className={`agent-activity ${compact ? "compact" : ""}`} aria-live="polite">
      {phase === "loading_embeddings" ? (
        <div className="agent-activity-spinner" aria-hidden="true" />
      ) : (
        <div className="agent-activity-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      )}
      <div className="agent-activity-text">
        <span className="agent-activity-label">{label}</span>
        <span className="agent-activity-timer">{formatElapsed(elapsedSeconds)}</span>
      </div>
      {phase === "loading_embeddings" && embeddingLoad && (
        <div className="agent-activity-progress-wrap">
          <div className="agent-activity-progress-track">
            <div
              className="agent-activity-progress-bar"
              style={{ width: `${Math.min(100, Math.max(0, embeddingLoad.progress))}%` }}
            />
          </div>
          <span className="agent-activity-progress-pct">
            {embeddingLoad.progress.toFixed(0)}%
          </span>
        </div>
      )}
    </div>
  );
}

export function formatResponseTime(seconds: number): string {
  return formatElapsed(seconds);
}
