from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.models import router as models_router
from app.api.routes.sites import router as sites_router
from app.config import get_settings
from app.db import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    # 使用 config.yaml 中的 db 配置初始化 MySQL
    init_db(settings.db)
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
    app.include_router(sites_router)

    return app


app = create_app()

