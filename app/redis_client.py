import os
import redis
import logging

logger = logging.getLogger(__name__)

# ================================
# REDIS CONFIG
# ================================
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379"  # local dev fallback only
)

# ================================
# REDIS CLIENT
# ================================
try:
    r = redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        health_check_interval=30,
    )

    # Test connection at import time (safe)
    r.ping()
    logger.info("[REDIS] Connected successfully")

except Exception as e:
    logger.error("[REDIS] Connection failed", exc_info=True)
    # Important: still raise so Render shows real error
    raise
