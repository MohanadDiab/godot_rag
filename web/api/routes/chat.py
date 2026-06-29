"""Chat streaming routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from scripts.agent.godot_agent import stream_ask
from web.api.schemas import ChatRequest
from web.api.sse import format_sse_event

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    if not request.api_key.strip():
        raise HTTPException(status_code=400, detail="api_key is required")

    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    async def event_generator():
        payload = [{"role": m.role, "content": m.content} for m in request.messages]
        async for event in stream_ask(
            payload,
            model=request.model,
            api_key=request.api_key.strip(),
        ):
            yield format_sse_event(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
