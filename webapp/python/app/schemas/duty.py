from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class Duty(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    area_id: int
    area_name: str
    scheduled_date: date
    status: str


class GenerateResult(BaseModel):
    created: int
