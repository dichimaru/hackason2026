from __future__ import annotations

from pydantic import BaseModel


class Employee(BaseModel):
    id: int
    name: str
    email: str
    department: str
    active: bool
