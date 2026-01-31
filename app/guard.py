from app.redis_client import r
from app.pricing import CPU_PRICE_PER_MIN

def should_stop(balance: float):
    # stop if < 5 minutes buffer
    return balance < (CPU_PRICE_PER_MIN * 5)
