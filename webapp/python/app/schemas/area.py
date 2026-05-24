from __future__ import annotations

from pydantic import BaseModel


class Area(BaseModel):
    id: int
    name: str
    description: str
