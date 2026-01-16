import os

BRAPI_TOKEN = os.getenv("BRAPI_TOKEN", "").strip()

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "5"))

# Cache TTLs (seconds)
TTL_BRAPI_QUOTE = int(os.getenv("TTL_BRAPI_QUOTE", "60"))
TTL_BRAPI_HISTORY = int(os.getenv("TTL_BRAPI_HISTORY", str(6 * 60 * 60)))
TTL_SGS_DAILY = int(os.getenv("TTL_SGS_DAILY", str(6 * 60 * 60)))
TTL_SGS_SLOW = int(os.getenv("TTL_SGS_SLOW", str(24 * 60 * 60)))
TTL_EXPECTATIONS = int(os.getenv("TTL_EXPECTATIONS", str(24 * 60 * 60)))
