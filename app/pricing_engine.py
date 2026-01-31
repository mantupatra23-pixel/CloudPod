from datetime import datetime
from app.models import Plan

def resolve_price(plan: Plan, resource: str):
    hour = datetime.utcnow().hour

    # peak hours (18–23 UTC)
    multiplier = 1.2 if 18 <= hour <= 23 else 1.0

    if resource == "cpu":
        return plan.cpu_price_per_min * multiplier
    if resource == "gpu":
        return plan.gpu_price_per_min * multiplier

    return 0
