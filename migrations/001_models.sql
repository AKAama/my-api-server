-- 模型表（MySQL），与 config.yaml 中 db.database 对应
-- 若使用 SQLAlchemy create_all，可不必手动执行本文件；本文件作为 schema 参考与手工迁移用

CREATE TABLE IF NOT EXISTS models (
    model_id   VARCHAR(36)   PRIMARY KEY,
    name       VARCHAR(128)  NOT NULL UNIQUE,
    endpoint   VARCHAR(512)  NOT NULL,
    api_key    VARCHAR(256)  NOT NULL,
    timeout    INT           NOT NULL DEFAULT 30,
    type       VARCHAR(64)   NULL,
    dimensions INT           NULL,
    created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
