from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import requests

from app.core.config import BRAPI_TOKEN, REQUEST_TIMEOUT

BRAPI_BASE = "https://brapi.dev/api"

def iso_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip().replace(",", ".")
        return float(s)
    except Exception:
        return None

def fetch_brapi_quote(ticker: str) -> Optional[Dict[str, Any]]:
    url = f"{BRAPI_BASE}/quote/{ticker}"
    params = {}
    if BRAPI_TOKEN:
        params["token"] = BRAPI_TOKEN

    try:
        r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        if not results:
            return None

        x = results[0]
        value = safe_float(x.get("regularMarketPrice"))
        change_abs = safe_float(x.get("regularMarketChange"))
        change_pct = safe_float(x.get("regularMarketChangePercent"))

        market_time = x.get("regularMarketTime")
        if isinstance(market_time, (int, float)) and market_time > 0:
            last_update = datetime.utcfromtimestamp(int(market_time)).replace(microsecond=0).isoformat() + "Z"
        else:
            last_update = iso_now()

        if value is None:
            return None

        return {"value": value, "change_abs": change_abs, "change_pct": change_pct, "last_update": last_update}
    except Exception:
        return None

def fetch_brapi_history_daily(ticker: str, range_: str = "1mo", interval: str = "1d") -> Optional[List[Dict[str, Any]]]:
    url = f"{BRAPI_BASE}/quote/{ticker}"
    params = {"range": range_, "interval": interval}
    if BRAPI_TOKEN:
        params["token"] = BRAPI_TOKEN

    try:
        r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        if not results:
            return None

        x = results[0]
        hist = x.get("historicalDataPrice")
        if not isinstance(hist, list) or not hist:
            return None

        out = []
        for row in hist:
            ts = row.get("date")
            close = safe_float(row.get("close"))
            if close is None:
                continue
            if isinstance(ts, (int, float)) and ts > 0:
                d = datetime.utcfromtimestamp(int(ts)).date().isoformat()
                out.append({"date": d, "close": close})

        if not out:
            return None
        out.sort(key=lambda x: x["date"])
        return out
    except Exception:
        return None
