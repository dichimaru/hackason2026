from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.api.deps import get_engine
from app.schemas.duty import Duty, GenerateResult
from app.services.duty_generator import generate_next_week

router = APIRouter(prefix="/duties", tags=["duties"])


@router.get("", response_model=list[Duty])
def list_duties(engine: Engine = Depends(get_engine)) -> list[Duty]:
    with engine.connect() as conn:
        rows = conn.execute(text(
            """
            SELECT d.id, d.employee_id, e.name AS employee_name,
                   d.area_id, a.name AS area_name,
                   d.scheduled_date, d.status
            FROM duties d
            JOIN employees e ON e.id = d.employee_id
            JOIN areas a     ON a.id = d.area_id
            ORDER BY d.scheduled_date, a.id
            """
        )).mappings().all()
    return [Duty(**dict(r)) for r in rows]


@router.post("/generate", response_model=GenerateResult)
def post_generate(engine: Engine = Depends(get_engine)) -> GenerateResult:
    try:
        created = generate_next_week(engine)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return GenerateResult(created=created)
