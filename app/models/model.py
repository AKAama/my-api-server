from typing import Optional, Dict, List

from pydantic import BaseModel, Field
from uuid import uuid4


class ModelBase(BaseModel):
    name: str = Field(..., description="模型名称")
    endpoint: str = Field(..., description="大模型 HTTP 接口地址")
    api_key: str = Field(..., description="访问大模型的 API Key")
    timeout: Optional[int] = Field(30, description="请求超时时间（秒）")
    type: Optional[str] = Field(None, description="模型类型")
    dimensions: Optional[int] = Field(None, description="向量维度等")


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


class ChatRequest(BaseModel):
    prompt: str


# 简单的内存存储，重启会丢数据。如需持久化可换成数据库。
MODELS: Dict[str, Model] = {}


def list_models() -> List[Model]:
    return list(MODELS.values())


def get_model_by_id(model_id: str) -> Optional[Model]:
    return MODELS.get(model_id)


def create_model_entry(req: ModelCreateRequest) -> Model:
    model_id = str(uuid4())
    model = Model(model_id=model_id, **req.dict())
    MODELS[model_id] = model
    return model


def save_model(model: Model) -> None:
    MODELS[model.model_id] = model


def delete_model_entry(model_id: str) -> Optional[Model]:
    model = MODELS.pop(model_id, None)
    return model


