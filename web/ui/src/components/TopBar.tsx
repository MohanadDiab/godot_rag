import { useEffect, useState } from "react";
import { fetchModels } from "../api";
import type { ModelInfo } from "../types";

const API_KEY_KEY = "godot_rag_api_key";
const MODEL_KEY = "godot_rag_model";
const CUSTOM_MODEL_KEY = "godot_rag_custom_model";

interface TopBarProps {
  apiKey: string;
  model: string;
  customModel: string;
  onApiKeyChange: (value: string) => void;
  onModelChange: (value: string) => void;
  onCustomModelChange: (value: string) => void;
  onNewChat: () => void;
}

export function TopBar({
  apiKey,
  model,
  customModel,
  onApiKeyChange,
  onModelChange,
  onCustomModelChange,
  onNewChat,
}: TopBarProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);

  useEffect(() => {
    fetchModels().then(setModels).catch(() => {
      setModels([
        { id: "gpt-5-nano", label: "gpt-5-nano" },
        { id: "gpt-4o-mini", label: "gpt-4o-mini" },
        { id: "gpt-4o", label: "gpt-4o" },
        { id: "custom", label: "Custom" },
      ]);
    });
  }, []);

  return (
    <header className="topbar">
      <div className="topbar-brand">Godot RAG</div>
      <div className="topbar-controls">
        <label className="field">
          <span>OpenAI key</span>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
            placeholder="sk-…"
            autoComplete="off"
          />
        </label>
        <label className="field">
          <span>Model</span>
          <select value={model} onChange={(e) => onModelChange(e.target.value)}>
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
        </label>
        {model === "custom" && (
          <label className="field">
            <span>Custom model</span>
            <input
              type="text"
              value={customModel}
              onChange={(e) => onCustomModelChange(e.target.value)}
              placeholder="gpt-4o-mini"
            />
          </label>
        )}
        <button type="button" className="btn secondary" onClick={onNewChat}>
          New chat
        </button>
      </div>
    </header>
  );
}

export function loadSettings() {
  return {
    apiKey: localStorage.getItem(API_KEY_KEY) ?? "",
    model: localStorage.getItem(MODEL_KEY) ?? "gpt-5-nano",
    customModel: localStorage.getItem(CUSTOM_MODEL_KEY) ?? "",
  };
}

export function saveSettings(apiKey: string, model: string, customModel: string) {
  localStorage.setItem(API_KEY_KEY, apiKey);
  localStorage.setItem(MODEL_KEY, model);
  localStorage.setItem(CUSTOM_MODEL_KEY, customModel);
}

export function resolveModel(model: string, customModel: string): string {
  return model === "custom" ? customModel.trim() || "gpt-4o-mini" : model;
}
