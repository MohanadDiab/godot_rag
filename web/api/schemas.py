"""Pydantic schemas for the web API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(description="user or assistant")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str = "gpt-5-nano"
    api_key: str = Field(min_length=1, description="OpenAI API key (never logged)")


class HealthResponse(BaseModel):
    status: str = "ok"


class ModelInfo(BaseModel):
    id: str
    label: str


class ModelsResponse(BaseModel):
    models: list[ModelInfo]
