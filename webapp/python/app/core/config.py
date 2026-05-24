"""アプリ設定。pydantic-settings に乗せ替える前提で os.environ ベース。"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env(key: str, default: str) -> str:
    return os.environ.get(key) or default


@dataclass(frozen=True)
class Settings:
    db_host: str = _env("DB_HOST", "db")
    db_port: str = _env("DB_PORT", "3306")
    db_user: str = _env("DB_USER", "cleaning")
    db_pass: str = _env("DB_PASS", "cleaning")
    db_name: str = _env("DB_NAME", "cleaning")

    @property
    def db_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


settings = Settings()
