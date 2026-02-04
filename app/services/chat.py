from typing import Dict, Any

import httpx
from fastapi.responses import StreamingResponse, JSONResponse
import codecs
import time

from app.config import get_settings

from app.models.model import Model


async def stream_to_client(model: Model, payload: Dict[str, Any]) -> StreamingResponse:
    """
    将下游大模型的 HTTP 流转换为 SSE 格式并转发给前端。
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Authorization": f"Bearer {model.api_key.strip()}",
    }
    timeout = model.timeout or 30

    async def event_stream():
        heartbeat_interval = get_settings().server.sse_heartbeat_seconds
        last_heartbeat = None
        decoder = codecs.getincrementaldecoder("utf-8")()
        buffer = ""
        def to_sse_line(text: str) -> str:
            if text.startswith(("data:", "event:", "id:", "retry:", ":")):
                return f"{text}\n"
            return f"data: {text}\n\n"

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", model.endpoint, json=payload, headers=headers) as r:
                async for chunk in r.aiter_bytes():
                    now = time.monotonic()
                    if last_heartbeat is None:
                        last_heartbeat = now
                    if heartbeat_interval > 0 and now - last_heartbeat >= heartbeat_interval:
                        last_heartbeat = now
                        yield ": ping\n\n"
                    if not chunk:
                        continue
                    buffer += decoder.decode(chunk)
                    if "\n" not in buffer:
                        # If upstream is SSE, wait for a full line before forwarding
                        if buffer.startswith("data:"):
                            continue
                        # Otherwise, emit chunk immediately as SSE data for typewriter effect
                        yield to_sse_line(buffer)
                        buffer = ""
                        continue
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.rstrip("\r")
                        if line == "":
                            yield "\n"
                            continue
                        yield to_sse_line(line)
                # flush remaining buffer
                tail = buffer.strip()
                if tail:
                    yield to_sse_line(tail)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def call_model_once(model: Model, payload: Dict[str, Any]) -> JSONResponse:
    """
    非流式场景：一次性请求下游大模型并返回 JSON。
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {model.api_key.strip()}",
    }
    timeout = model.timeout or 30

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(model.endpoint, json=payload, headers=headers)
        except httpx.HTTPError as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=502, detail=f"大模型请求失败: {e}") from e

    try:
        content = resp.json()
    except Exception:
        content = {"error": resp.text or f"HTTP {resp.status_code}"}

    return JSONResponse(status_code=resp.status_code, content=content)
