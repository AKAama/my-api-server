from typing import Dict

from fastapi import APIRouter, HTTPException, Query, Body, Request

from app.models.model import (
    Model,
    ModelCreateRequest,
    ModelUpdateRequest,
    ChatRequest,
    MODELS,
    list_models,
    get_model_by_id,
    create_model_entry,
    save_model,
    delete_model_entry,
)
from app.models.response import APIResponse, success, error
from app.services.chat import stream_to_client, call_model_once


router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.post("/create", response_model=APIResponse)
async def create_model(req: ModelCreateRequest) -> APIResponse:
    for m in MODELS.values():
        if m.name == req.name:
            return error(409, "模型名称已存在")
    model = create_model_entry(req)
    return success(model, "成功创建模型")


@router.get("/{model_id}", response_model=APIResponse)
async def get_model(model_id: str) -> APIResponse:
    model = get_model_by_id(model_id)
    if not model:
        return error(404, "模型不存在")
    return success(model, "查询成功")


@router.get("/get", response_model=APIResponse)
async def get_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
) -> APIResponse:
    all_models = list_models()
    total = len(all_models)
    start = (page - 1) * page_size
    end = start + page_size
    page_models = all_models[start:end]
    return success(
        {
            "list": page_models,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "查询模型列表成功",
    )


@router.put("/{model_id}", response_model=APIResponse)
async def update_model(model_id: str, req: ModelUpdateRequest) -> APIResponse:
    model = get_model_by_id(model_id)
    if not model:
        return error(404, "模型不存在")

    if req.name and req.name != model.name:
        for mid, m in MODELS.items():
            if mid != model_id and m.name == req.name:
                return error(409, "模型名称已存在")

    update_data = req.dict(exclude_unset=True)
    updated = model.copy(update=update_data)
    save_model(updated)
    return success(updated, "成功更新模型")


@router.delete("/{model_id}", response_model=APIResponse)
async def delete_model(model_id: str) -> APIResponse:
    model = delete_model_entry(model_id)
    if not model:
        return error(404, "模型不存在")
    return success(model, "成功删除模型")


@router.post("/chat/{model_id}")
async def chat_with_model(
    model_id: str,
    request: Request,
    req: ChatRequest = Body(...),
):
    model = get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    model_name = model.type or model.name
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": req.prompt,
            }
        ],
    }

    stream = request.query_params.get("stream") == "1"
    if stream:
        return await stream_to_client(model, payload)

    return await call_model_once(model, payload)


