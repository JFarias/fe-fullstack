from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional

CACHE: Dict[str, Dict[str, Any]] = {}

def cache_get_fresh(key: str) -> Optional[Dict[str, Any]]:
    item = CACHE.get(key)
    if not item:
        return None
    expires_at = item.get("expires_at")
    if not expires_at:
        return None
    if datetime.utcnow().timestamp() >= float(expires_at):
        return None
    return item.get("value")

def cache_get_last_known(key: str) -> Optional[Dict[str, Any]]:
    item = CACHE.get(key)
    if not item:
        return None
    return item.get("last_known")

def cache_set(key: str, value: Dict[str, Any], ttl_seconds: int) -> None:
    now_ts = datetime.utcnow().timestamp()
    CACHE[key] = {
        "value": value,
        "expires_at": now_ts + ttl_seconds,
        "last_known": value,
        "last_known_at": now_ts
    }

def cache_last_known_at_iso(key: str) -> Optional[str]:
    item = CACHE.get(key)
    if not item:
        return None
    ts = item.get("last_known_at")
    if not isinstance(ts, (int, float)):
        return None
    return datetime.utcfromtimestamp(ts).replace(microsecond=0).isoformat() + "Z"