from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import requests

from app.core.config import REQUEST_TIMEOUT
from app.core.cache import cache_get_fresh, cache_get_last_known, cache_set, cache_last_known_at_iso

EXPECT_OLINDA_BASE = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata"

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

def fetch_bcb_inflation_expectations_12m_median(indicador: str = "IPCA", prefer_smooth: bool = True) -> Optional[Dict[str, Any]]:
    url = f"{EXPECT_OLINDA_BASE}/ExpectativasMercadoInflacao12Meses"
    params = {
        "$format": "json",
        "$top": "10",
        "$orderby": "Data desc",
        "$select": "Indicador,Data,Suavizada,Media,Mediana,Minimo,Maximo,numeroRespondentes",
        "$filter": f"Indicador eq '{indicador}'",
    }

    try:
        r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
        rows = payload.get("value")
        if not isinstance(rows, list) or not rows:
            return None
    except Exception:
        return None

    def is_smooth(row: Dict[str, Any]) -> bool:
        s = row.get("Suavizada")
        if isinstance(s, bool):
            return s
        if s is None:
            return False
        s_str = str(s).strip().lower()
        return s_str in ("true", "1", "s", "sim", "yes")

    chosen = None
    if prefer_smooth:
        smooth_rows = [x for x in rows if is_smooth(x)]
        chosen = smooth_rows[0] if smooth_rows else rows[0]
    else:
        chosen = rows[0]

    median = safe_float(chosen.get("Mediana"))
    if median is None:
        return None

    last_update_raw = chosen.get("Data")
    last_update = iso_now()
    if last_update_raw:
        s = str(last_update_raw).strip()
        if "T" in s:
            last_update = s if s.endswith("Z") else (s + "Z")
        else:
            last_update = s + "T00:00:00Z"

    return {"value": median, "last_update": last_update, "raw": chosen}

def get_cached_inflation_expectations_12m(
    indicador: str,
    prefer_smooth: bool,
    ttl_seconds: int
) -> Dict[str, Any]:
    cache_key = f"expectations:{indicador}:median:smooth={prefer_smooth}"

    fresh = cache_get_fresh(cache_key)
    if fresh:
        return {
            "data": fresh,
            "cache": {
                "hit": True,
                "stale": False,
                "from_fallback": False,
                "ttl_seconds": ttl_seconds,
                "last_known_at": cache_last_known_at_iso(cache_key),
            }
        }

    fetched = fetch_bcb_inflation_expectations_12m_median(indicador=indicador, prefer_smooth=prefer_smooth)
    if fetched:
        cache_set(cache_key, fetched, ttl_seconds=ttl_seconds)
        return {
            "data": fetched,
            "cache": {
                "hit": False,
                "stale": False,
                "from_fallback": False,
                "ttl_seconds": ttl_seconds,
                "last_known_at": cache_last_known_at_iso(cache_key),
            }
        }

    last_known = cache_get_last_known(cache_key)
    if last_known:
        return {
            "data": last_known,
            "cache": {
                "hit": False,
                "stale": True,
                "from_fallback": True,
                "ttl_seconds": ttl_seconds,
                "last_known_at": cache_last_known_at_iso(cache_key),
            }
        }

    return {
        "data": None,
        "cache": {
            "hit": False,
            "stale": True,
            "from_fallback": False,
            "ttl_seconds": ttl_seconds,
            "last_known_at": None,
        }
    }
