from typing import Any, Optional

from pydantic import BaseModel


class APIResponse(BaseModel):
    status: int
    data: Optional[Any] = None
    msg: str


def success(data: Any = None, msg: str = "success") -> APIResponse:
    return APIResponse(status=200, data=data, msg=msg)


def error(status: int, msg: str) -> APIResponse:
    return APIResponse(status=status, data=None, msg=msg)


