"""FastAPI エントリポイント。ルータ登録だけに留める。"""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import areas, duties, employees, health

app = FastAPI(title="cleaning-app", version="0.1.0")

app.include_router(health.router, prefix="/api")
app.include_router(employees.router, prefix="/api")
app.include_router(areas.router, prefix="/api")
app.include_router(duties.router, prefix="/api")
