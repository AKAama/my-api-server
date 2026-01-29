from functools import lru_cache
import os
from pathlib import Path
from typing import Optional, Dict

import yaml
from pydantic import BaseModel


class ServerConfig(BaseModel):
    port: int = 3000


class DBConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str
    database: str
    maxConnections: int


class MilvusConfig(BaseModel):
    host: str
    username: str
    password: str
    dbname: str


class NatsAccount(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    seed: Optional[str] = None
    nkey: Optional[str] = None


class NatsConfig(BaseModel):
    endpoint: str
    subject: str
    streamName: str
    articleSubject: str
    articleConsumerName: str
    imagesProcSubject: str
    imagesProcConsumerName: str
    clientId: str
    defaultAccountName: str
    account: Dict[str, NatsAccount]


class Settings(BaseModel):
    server: ServerConfig
    db: DBConfig
    milvus: MilvusConfig
    nats: NatsConfig


def _default_config_path() -> Path:
    base_dir = Path(__file__).resolve().parents[2]
    return base_dir / "my-api-server" / "etc" / "config.yaml"


@lru_cache()
def get_settings(config_path: Optional[str] = None) -> Settings:
    if config_path:
        path = Path(config_path)
    else:
        env_path = os.getenv("CONFIG")
        path = Path(env_path) if env_path else _default_config_path()
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return Settings(**raw)


