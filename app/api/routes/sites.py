from fastapi import APIRouter

from app.models.model import (
    SiteCreateRequest,
    SiteUpdateRequest,
    list_sites,
    get_site_by_id,
    create_site_entry,
    save_site,
    delete_site_entry,
)
from app.models.response import APIResponse, success, error


router = APIRouter(prefix="/api/v1/sites", tags=["sites"])


@router.post("/create", response_model=APIResponse)
async def create_site(req: SiteCreateRequest) -> APIResponse:
    site = create_site_entry(req)
    return success(site, "成功创建站点")


@router.get("/get", response_model=APIResponse)
async def get_sites() -> APIResponse:
    sites = list_sites()
    return success(
        {
            "list": sites,
            "total": len(sites),
        },
        "查询站点列表成功",
    )


@router.get("/{site_id}", response_model=APIResponse)
async def get_site(site_id: int) -> APIResponse:
    """获取单个站点"""
    site = get_site_by_id(site_id)
    if not site:
        return error(404, "站点不存在")
    return success(site, "查询成功")


@router.put("/{site_id}", response_model=APIResponse)
async def update_site(site_id: int, req: SiteUpdateRequest) -> APIResponse:
    site = get_site_by_id(site_id)
    if not site:
        return error(404, "站点不存在")

    update_data = req.model_dump(exclude_unset=True)
    updated = site.model_copy(update=update_data)
    save_site(updated)
    return success(updated, "成功更新站点")


@router.delete("/{site_id}", response_model=APIResponse)
async def delete_site(site_id: int) -> APIResponse:
    site = delete_site_entry(site_id)
    if not site:
        return error(404, "站点不存在")
    return success(site, "成功删除站点")
