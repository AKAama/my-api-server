from typing import Dict, Any

import httpx
from fastapi.responses import StreamingResponse, JSONResponse

from app.models.model import Model


async def stream_to_client(model: Model, payload: Dict[str, Any]) -> StreamingResponse:
  """
  将下游大模型的 HTTP 流直接转发给前端，用于 fetch stream / SSE 等场景。
  """
  headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {model.api_key.strip()}",
  }

  timeout = model.timeout or 30

  async def event_stream():
      async with httpx.AsyncClient(timeout=timeout) as client:
          async with client.stream("POST", model.endpoint, json=payload, headers=headers) as r:
              async for chunk in r.aiter_bytes():
                  yield chunk

  return StreamingResponse(event_stream(), media_type="application/json")


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
      resp = await client.post(model.endpoint, json=payload, headers=headers)

  # 直接转发状态码和 JSON 内容
  return JSONResponse(status_code=resp.status_code, content=resp.json())


