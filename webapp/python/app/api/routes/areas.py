from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.api.deps import get_engine
from app.schemas.area import Area

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[Area])
def list_areas(engine: Engine = Depends(get_engine)) -> list[Area]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name, description FROM areas ORDER BY id")
        ).mappings().all()
    return [Area(**dict(r)) for r in rows]
