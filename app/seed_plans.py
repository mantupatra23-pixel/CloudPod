from app.db import SessionLocal
from app.models import Plan

def seed_plans():
    db = SessionLocal()
    if db.query(Plan).count() > 0:
        return

    plans = [
        Plan(
            name="starter",
            monthly_price=0,
            cpu_price_per_min=2,
            gpu_price_per_min=0,
            max_gpu=0,
            priority=0
        ),
        Plan(
            name="creator",
            monthly_price=999,
            cpu_price_per_min=1.5,
            gpu_price_per_min=8,
            max_gpu=1,
            priority=1
        ),
        Plan(
            name="pro",
            monthly_price=2999,
            cpu_price_per_min=1,
            gpu_price_per_min=6,
            max_gpu=2,
            priority=2
        )
    ]

    db.add_all(plans)
    db.commit()
    db.close()
