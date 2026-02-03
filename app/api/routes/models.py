import httpx
from fastapi import APIRouter, HTTPException, Body, Request, Query

from app.models.model import (
    ModelCreateRequest,
    ModelUpdateRequest,
    ModelGetRequest,
    ChatRequest,
    list_models,
    get_model_by_id,
    get_model_by_name,
    exists_model_with_name_excluding,
    create_model_entry,
    save_model,
    delete_model_entry,
)
from app.models.response import APIResponse, success, error
from app.services.chat import stream_to_client, call_model_once


router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.post("/create", response_model=APIResponse)
async def create_model(req: ModelCreateRequest) -> APIResponse:
    if get_model_by_name(req.name) is not None:
        return error(409, "模型名称已存在")
    model = create_model_entry(req)
    return success(model, "成功创建模型")


async def _do_get_models(
    req: ModelGetRequest,
) -> APIResponse:
    """获取模型，支持单个查询或列表查询"""
    # 如果传了 model_id，查询单个模型
    if req.model_id:
        model = get_model_by_id(req.model_id)
        if not model:
            return error(404, "模型不存在")
        return success(model, "查询成功")

    # 否则查询列表
    all_models = list_models()
    total = len(all_models)
    start = (req.page - 1) * req.page_size
    end = start + req.page_size
    page_models = all_models[start:end]
    return success(
        {
            "list": page_models,
            "total": total,
            "page": req.page,
            "page_size": req.page_size,
        },
        "查询模型列表成功",
    )


@router.post("/get", response_model=APIResponse)
async def get_models_post(req: ModelGetRequest) -> APIResponse:
    """POST 方式获取模型"""
    return await _do_get_models(req)


@router.get("/get", response_model=APIResponse)
async def get_models_get(
    model_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
) -> APIResponse:
    """GET 方式获取模型"""
    req = ModelGetRequest(model_id=model_id, page=page, page_size=page_size)
    return await _do_get_models(req)


@router.put("/{model_id}", response_model=APIResponse)
async def update_model(model_id: str, req: ModelUpdateRequest) -> APIResponse:
    model = get_model_by_id(model_id)
    if not model:
        return error(404, "模型不存在")

    if req.name and req.name != model.name and exists_model_with_name_excluding(req.name, model_id):
        return error(409, "模型名称已存在")

    update_data = req.model_dump(exclude_unset=True)
    updated = model.model_copy(update=update_data)
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
        return error(404, "模型不存在")

    # 与 Go 一致：API Key 校验
    api_key = (model.api_key or "").strip()
    if not api_key:
        return error(500, "API Key 为空")
    if any(c in api_key for c in "\r\n\t "):
        return error(500, "API Key 包含非法字符")

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

    try:
        return await call_model_once(model, payload)
    except HTTPException as e:
        return error(e.status_code, e.detail if isinstance(e.detail, str) else str(e.detail))


