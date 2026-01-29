from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.models import router as models_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="MyAPI Python Server", version="0.1.0")

    # 将配置挂到应用状态，方便后续在路由或服务中使用
    app.state.settings = settings

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 路由
    app.include_router(models_router)

    return app


app = create_app()

