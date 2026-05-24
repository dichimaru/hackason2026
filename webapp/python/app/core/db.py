"""SQLAlchemy エンジン初期化。MySQL 起動待ちのため最大30回リトライ。"""
from __future__ import annotations

import time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import settings


def _build_engine() -> Engine:
    last_err: Exception | None = None
    for i in range(30):
        try:
            eng = create_engine(settings.db_url, pool_pre_ping=True, future=True)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            return eng
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"waiting for DB... ({i}): {e}")
            time.sleep(2)
    raise RuntimeError(f"failed to connect db: {last_err}")


engine: Engine = _build_engine()
