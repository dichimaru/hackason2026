from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.api.deps import get_engine
from app.schemas.employee import Employee

router = APIRouter(prefix="/people", tags=["people"])


@router.get("", response_model=list[Employee])
def list_employees(engine: Engine = Depends(get_engine)) -> list[Employee]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name, email, department, active FROM employees ORDER BY id")
        ).mappings().all()
    return [
        Employee(
            id=r["id"],
            name=r["name"],
            email=r["email"],
            department=r["department"],
            active=bool(r["active"]),
        )
        for r in rows
    ]
