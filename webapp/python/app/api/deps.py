"""ルータ依存性: グローバルなエンジンを必要なら DI 経由で差し替え可能に。"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from app.core.db import engine


def get_engine() -> Engine:
    return engine
