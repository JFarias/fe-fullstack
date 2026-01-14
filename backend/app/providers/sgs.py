from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple
import requests

from app.core.config import REQUEST_TIMEOUT

SGS_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"

def to_ddmmyyyy(d: date) -> str:
    return d.strftime("%d/%m/%Y")

def parse_sgs_date(ddmmyyyy: str) -> str:
    from datetime import datetime
    return datetime.strptime(ddmmyyyy, "%d/%m/%Y").date().isoformat()

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

def fetch_sgs_series(code: int, start: date, end: date) -> List[Dict[str, Any]]:
    url = SGS_BASE.format(code=code)
    params = {
        "formato": "json",
        "dataInicial": to_ddmmyyyy(start),
        "dataFinal": to_ddmmyyyy(end),
    }
    r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    raw = r.json()

    out = []
    for row in raw:
        d = row.get("data")
        v = row.get("valor")
        if not d:
            continue
        dv = safe_float(v)
        if dv is None:
            continue
        out.append({"date": parse_sgs_date(d), "value": dv})

    out.sort(key=lambda x: x["date"])
    return out

def last_and_prev(points: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if len(points) < 2:
        return None, None
    return points[-1], points[-2]
