"""
数据库连接与表初始化。
从 config.yaml 的 db 配置读取 MySQL 连接信息，与 get_settings() 一致。
"""
from contextlib import contextmanager
from datetime import datetime
from urllib.parse import quote_plus

from sqlalchemy import create_engine, Integer, String, DateTime, BigInteger
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column

from app.config import DBConfig


class Base(DeclarativeBase):
    pass


class ModelRecord(Base):
    """模型表 ORM，对应数据库中的 t_model 表。"""
    __tablename__ = "t_model"

    model_id: Mapped[str] = mapped_column("model_id", String(64), primary_key=True)
    name: Mapped[str] = mapped_column("name", String(255), unique=True, nullable=False)
    endpoint: Mapped[str] = mapped_column("endpoint", String(255), nullable=False)
    api_key: Mapped[str] = mapped_column("api_key", String(255), nullable=False)
    timeout: Mapped[int] = mapped_column("timeout", BigInteger, nullable=False, default=30)
    type: Mapped[str] = mapped_column("type", String(255), nullable=False)
    dimensions: Mapped[int] = mapped_column("dimensions", BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime | None] = mapped_column("created_at", DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column("updated_at", DateTime, nullable=True)


class SiteRecord(Base):
    """站点表 ORM，对应数据库中的 t_site 表。"""
    __tablename__ = "t_site"

    site_id: Mapped[int] = mapped_column("site_id", Integer, primary_key=True)
    site_name: Mapped[str | None] = mapped_column("site_name", String(255), nullable=True)


_engine = None
_SessionLocal = None


def _build_mysql_url(cfg: DBConfig) -> str:
    """从 config.yaml 的 db 配置拼 MySQL URL。"""
    password = quote_plus(cfg.password) if cfg.password else ""
    return (
        f"mysql+pymysql://{cfg.username}:{password}@{cfg.host}:{cfg.port}/{cfg.database}"
    )


def init_db(db_config: DBConfig) -> None:
    """使用 config.yaml 中的 db 配置初始化 MySQL 连接。"""
    global _engine, _SessionLocal
    if _engine is not None:
        return
    url = _build_mysql_url(db_config)
    _engine = create_engine(
        url,
        pool_size=min(db_config.maxConnections, 20),
        pool_pre_ping=True,
        echo=False,
    )
    # 不自动创建表，使用数据库中已有的表
    # Base.metadata.create_all(_engine)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)



@contextmanager
def get_db_session():
    """获取数据库 session（上下文管理器）。"""
    if _SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()