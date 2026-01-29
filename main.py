"""
兼容入口文件，便于使用 `uvicorn main:app` 启动。
实际应用代码位于 `app/` 包内。
"""

from app.main import app  # noqa: F401
from app.config import get_settings


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.server.port,
        reload=True,
    )

