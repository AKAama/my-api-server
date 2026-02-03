from typing import Optional, List

from pydantic import BaseModel, Field
from uuid import uuid4
from sqlalchemy import select

from app.db import get_db_session, ModelRecord, SiteRecord


class ModelBase(BaseModel):
    name: str = Field(..., description="模型名称")
    endpoint: str = Field(..., description="大模型 HTTP 接口地址")
    api_key: str = Field(..., description="访问大模型的 API Key")
    timeout: int = Field(30, description="请求超时时间（秒）")
    type: str = Field("", description="模型类型")
    dimensions: int = Field(0, description="向量维度")


class ModelCreateRequest(ModelBase):
    pass


class ModelUpdateRequest(BaseModel):
    name: Optional[str] = None
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    timeout: Optional[int] = None
    type: Optional[str] = None
    dimensions: Optional[int] = None


class Model(ModelBase):
    model_id: str


class ModelGetRequest(BaseModel):
    model_id: Optional[str] = None
    page: int = 1
    page_size: int = 10


class ChatRequest(BaseModel):
    prompt: str


def _record_to_model(r: ModelRecord) -> Model:
    """ORM 记录转 Pydantic 模型。"""
    return Model(
        model_id=r.model_id,
        name=r.name,
        endpoint=r.endpoint,
        api_key=r.api_key,
        timeout=r.timeout,
        type=r.type,
        dimensions=r.dimensions,
    )


def list_models() -> List[Model]:
    """查询模型列表（不分页，由路由层做分页）。"""
    with get_db_session() as session:
        result = session.execute(select(ModelRecord).order_by(ModelRecord.created_at))
        rows = result.scalars().all()
        return [_record_to_model(r) for r in rows]


def get_model_by_id(model_id: str) -> Optional[Model]:
    """按 model_id 查询单个模型。"""
    with get_db_session() as session:
        r = session.get(ModelRecord, model_id)
        return _record_to_model(r) if r else None


def get_model_by_name(name: str) -> Optional[Model]:
    """按 name 查询单个模型（用于唯一性校验）。"""
    with get_db_session() as session:
        r = session.execute(select(ModelRecord).where(ModelRecord.name == name)).scalars().one_or_none()
        return _record_to_model(r) if r else None


def exists_model_with_name_excluding(name: str, exclude_model_id: str) -> bool:
    """是否存在同名模型（排除指定 model_id）。"""
    with get_db_session() as session:
        r = session.execute(
            select(ModelRecord).where(
                ModelRecord.name == name,
                ModelRecord.model_id != exclude_model_id,
            )
        ).scalars().first()
        return r is not None


def create_model_entry(req: ModelCreateRequest) -> Model:
    """创建模型并落库。"""
    model_id = str(uuid4())
    timeout = req.timeout if req.timeout > 0 else 30
    with get_db_session() as session:
        record = ModelRecord(
            model_id=model_id,
            name=req.name,
            endpoint=req.endpoint,
            api_key=req.api_key,
            timeout=timeout,
            type=req.type,
            dimensions=req.dimensions,
        )
        session.add(record)
        session.flush()
        return _record_to_model(record)


def save_model(model: Model) -> None:
    """更新模型并落库。"""
    with get_db_session() as session:
        record = session.get(ModelRecord, model.model_id)
        if not record:
            return
        record.name = model.name
        record.endpoint = model.endpoint
        record.api_key = model.api_key
        record.timeout = model.timeout
        record.type = model.type
        record.dimensions = model.dimensions


def delete_model_entry(model_id: str) -> Optional[Model]:
    """删除模型并返回被删记录（用于响应）。"""
    with get_db_session() as session:
        record = session.get(ModelRecord, model_id)
        if not record:
            return None
        model = _record_to_model(record)
        session.delete(record)
        return model


# ============ Site Pydantic Models ============

class SiteBase(BaseModel):
    site_name: Optional[str] = Field(None, description="站点名称")


class SiteCreateRequest(SiteBase):
    pass


class SiteUpdateRequest(BaseModel):
    site_name: Optional[str] = Field(None, description="站点名称")


class Site(BaseModel):
    site_id: int
    site_name: Optional[str] = None


def _record_to_site(r: SiteRecord) -> Site:
    """ORM 记录转 Pydantic Site 模型。"""
    return Site(
        site_id=r.site_id,
        site_name=r.site_name,
    )


def list_sites() -> List[Site]:
    """查询站点列表。"""
    with get_db_session() as session:
        result = session.execute(select(SiteRecord).order_by(SiteRecord.site_id))
        rows = result.scalars().all()
        return [_record_to_site(r) for r in rows]


def get_site_by_id(site_id: int) -> Optional[Site]:
    """按 site_id 查询单个站点。"""
    with get_db_session() as session:
        r = session.get(SiteRecord, site_id)
        return _record_to_site(r) if r else None


def create_site_entry(req: SiteCreateRequest) -> Site:
    """创建站点并落库。"""
    with get_db_session() as session:
        # 获取当前最大 site_id
        max_id = session.execute(select(SiteRecord.site_id).order_by(SiteRecord.site_id.desc())).scalar()
        new_id = (max_id or 0) + 1
        record = SiteRecord(
            site_id=new_id,
            site_name=req.site_name,
        )
        session.add(record)
        session.flush()
        return _record_to_site(record)


def save_site(site: Site) -> None:
    """更新站点并落库。"""
    with get_db_session() as session:
        record = session.get(SiteRecord, site.site_id)
        if not record:
            return
        record.site_name = site.site_name


def delete_site_entry(site_id: int) -> Optional[Site]:
    """删除站点并返回被删记录。"""
    with get_db_session() as session:
        record = session.get(SiteRecord, site_id)
        if not record:
            return None
        site = _record_to_site(record)
        session.delete(record)
        return site
