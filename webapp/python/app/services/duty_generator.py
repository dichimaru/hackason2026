"""翌週5営業日分の当番を、社員からランダム公平抽選で生成。"""
from __future__ import annotations

import random
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Engine


def generate_next_week(engine: Engine) -> int:
    with engine.begin() as conn:
        emp_ids = [r[0] for r in conn.execute(
            text("SELECT id FROM employees WHERE active = 1")
        ).all()]
        area_ids = [r[0] for r in conn.execute(text("SELECT id FROM areas")).all()]
        if not emp_ids or not area_ids:
            raise ValueError("employees or areas is empty")

        random.shuffle(emp_ids)
        created = 0
        idx = 0
        for day in range(7, 12):
            d = (date.today() + timedelta(days=day)).isoformat()
            for area_id in area_ids:
                emp_id = emp_ids[idx % len(emp_ids)]
                idx += 1
                conn.execute(text(
                    "INSERT INTO duties (employee_id, area_id, scheduled_date, status) "
                    "VALUES (:e, :a, :d, 'pending')"
                ), {"e": emp_id, "a": area_id, "d": d})
                created += 1
    return created
