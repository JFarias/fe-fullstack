from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import math
import statistics

from app.core.config import (
    TTL_BRAPI_HISTORY, TTL_BRAPI_QUOTE, TTL_EXPECTATIONS, TTL_SGS_DAILY, TTL_SGS_SLOW
)
from app.core.cache import cache_get_fresh, cache_get_last_known, cache_set, cache_last_known_at_iso

from app.providers.sgs import fetch_sgs_series, last_and_prev
from app.providers.brapi import fetch_brapi_quote, fetch_brapi_history_daily
from app.providers.expectations import get_cached_inflation_expectations_12m
from app.providers.brapi import iso_now as iso_now_brapi

SGS_CODES = {
    "selic": 11,
    "ipca_mm": 433,
    "usdbrl": 1,
    "unemployment": 4391,
    "gdp": 11752,
}

BRAPI_TICKERS = {"ibov": "^BVSP", "usdbrl": "USDBRL"}

def pct_change(new: float, old: float) -> Optional[float]:
    if old == 0:
        return None
    return (new / old - 1.0) * 100.0

def annualized_vol_from_closes(closes: List[float], window_returns: int = 20, trading_days: int = 252) -> Optional[float]:
    if len(closes) < window_returns + 1:
        return None
    tail = closes[-(window_returns + 1):]
    returns = []
    for i in range(1, len(tail)):
        if tail[i - 1] <= 0 or tail[i] <= 0:
            return None
        returns.append(math.log(tail[i] / tail[i - 1]))
    if len(returns) < 2:
        return None
    stdev = statistics.pstdev(returns)
    return stdev * math.sqrt(trading_days) * 100.0

def compute_ipca_12m_from_mm(ipca_mm_points: List[Dict[str, Any]]) -> Optional[float]:
    if len(ipca_mm_points) < 12:
        return None
    tail = ipca_mm_points[-12:]
    factor = 1.0
    for p in tail:
        factor *= (1.0 + (p["value"] / 100.0))
    return (factor - 1.0) * 100.0

def _cached_fetch(key: str, ttl: int, fn):
    fresh = cache_get_fresh(key)
    if fresh:
        return fresh, {"hit": True, "stale": False, "from_fallback": False, "ttl_seconds": ttl, "last_known_at": cache_last_known_at_iso(key)}
    data = fn()
    if data is not None:
        cache_set(key, data, ttl_seconds=ttl)
        return data, {"hit": False, "stale": False, "from_fallback": False, "ttl_seconds": ttl, "last_known_at": cache_last_known_at_iso(key)}
    last_known = cache_get_last_known(key)
    if last_known is not None:
        return last_known, {"hit": False, "stale": True, "from_fallback": True, "ttl_seconds": ttl, "last_known_at": cache_last_known_at_iso(key)}
    return None, {"hit": False, "stale": True, "from_fallback": False, "ttl_seconds": ttl, "last_known_at": None}

def build_homepage_payload() -> Dict[str, Any]:
    today = date.today()
    start_90d = today - timedelta(days=90)
    start_2y = today - timedelta(days=900)
    start_10y = today - timedelta(days=3650)

    # SGS (cache)
    selic_points, selic_cache = _cached_fetch(
        "sgs:selic",
        TTL_SGS_DAILY,
        lambda: fetch_sgs_series(SGS_CODES["selic"], start_90d, today)
    )
    ipca_points, ipca_cache = _cached_fetch(
        "sgs:ipca",
        TTL_SGS_SLOW,
        lambda: fetch_sgs_series(SGS_CODES["ipca_mm"], start_2y, today)
    )
    usd_points, usd_cache = _cached_fetch(
        "sgs:usdbrl",
        TTL_SGS_DAILY,
        lambda: fetch_sgs_series(SGS_CODES["usdbrl"], start_90d, today)
    )
    unemp_points, unemp_cache = _cached_fetch(
        "sgs:unemployment",
        TTL_SGS_SLOW,
        lambda: fetch_sgs_series(SGS_CODES["unemployment"], start_10y, today)
    )
    gdp_points, gdp_cache = _cached_fetch(
        "sgs:gdp",
        TTL_SGS_SLOW,
        lambda: fetch_sgs_series(SGS_CODES["gdp"], start_10y, today)
    )

    selic_last, selic_prev = last_and_prev(selic_points or [])
    ipca_last, ipca_prev = last_and_prev(ipca_points or [])
    usd_last, usd_prev = last_and_prev(usd_points or [])
    unemp_last, unemp_prev = last_and_prev(unemp_points or [])
    gdp_last, gdp_prev = last_and_prev(gdp_points or [])

    ipca_12m = compute_ipca_12m_from_mm(ipca_points or [])

    # BRAPI quote (cache)
    ibov_quote, ibov_quote_cache = _cached_fetch(
        "brapi:quote:^BVSP",
        TTL_BRAPI_QUOTE,
        lambda: fetch_brapi_quote(BRAPI_TICKERS["ibov"])
    )

    # BRAPI history (cache) for vol
    ibov_hist, ibov_hist_cache = _cached_fetch(
        "brapi:hist:^BVSP:1mo:1d",
        TTL_BRAPI_HISTORY,
        lambda: fetch_brapi_history_daily(BRAPI_TICKERS["ibov"], range_="1mo", interval="1d")
    )

    usd_hist, usd_hist_cache = _cached_fetch(
        "brapi:hist:USDBRL:1mo:1d",
        TTL_BRAPI_HISTORY,
        lambda: fetch_brapi_history_daily(BRAPI_TICKERS["usdbrl"], range_="1mo", interval="1d")
    )

    ibov_vol = None
    if ibov_hist:
        closes = [x["close"] for x in ibov_hist if isinstance(x.get("close"), (int, float))]
        ibov_vol = annualized_vol_from_closes(closes)

    usd_vol = None
    if usd_hist:
        closes = [x["close"] for x in usd_hist if isinstance(x.get("close"), (int, float))]
        usd_vol = annualized_vol_from_closes(closes)
    else:
        # fallback to SGS values as closes
        if usd_points:
            closes = [x["value"] for x in usd_points[-60:]]
            usd_vol = annualized_vol_from_closes(closes)

    # Expectations (cached with expired fallback inside)
    exp_bundle = get_cached_inflation_expectations_12m("IPCA", True, TTL_EXPECTATIONS)
    expectations = exp_bundle["data"]

    # Real rate approx
    real_rate = None
    if selic_last and ipca_12m is not None:
        real_rate = selic_last["value"] - ipca_12m

    # Build sections
    top_cards: List[Dict[str, Any]] = []

    # IBOV
    top_cards.append({
        "key": "ibov",
        "label": "IBOV",
        "value": ibov_quote["value"] if ibov_quote else None,
        "unit": "pts",
        "change_1d": ibov_quote.get("change_pct") if ibov_quote else None,
        "change_1d_unit": "%",
        "last_update": ibov_quote.get("last_update") if ibov_quote else iso_now_brapi(),
    })

    # USD/BRL (SGS)
    top_cards.append({
        "key": "usdbrl",
        "label": "USD/BRL",
        "value": usd_last["value"] if usd_last else None,
        "unit": "BRL",
        "change_1d": (usd_last["value"] - usd_prev["value"]) if (usd_last and usd_prev) else None,
        "change_1d_unit": "BRL",
        "last_update": (usd_last["date"] + "T00:00:00Z") if usd_last else iso_now_brapi(),
    })

    # SELIC
    top_cards.append({
        "key": "selic",
        "label": "SELIC",
        "value": selic_last["value"] if selic_last else None,
        "unit": "% a.a.",
        "change_1d": (selic_last["value"] - selic_prev["value"]) if (selic_last and selic_prev) else None,
        "change_1d_unit": "p.p.",
        "last_update": (selic_last["date"] + "T00:00:00Z") if selic_last else iso_now_brapi(),
    })

    # IPCA m/m last
    top_cards.append({
        "key": "ipca_last",
        "label": "IPCA (m/m)",
        "value": ipca_last["value"] if ipca_last else None,
        "unit": "%",
        "change_1d": (ipca_last["value"] - ipca_prev["value"]) if (ipca_last and ipca_prev) else None,
        "change_1d_unit": "p.p.",
        "last_update": (ipca_last["date"] + "T00:00:00Z") if ipca_last else iso_now_brapi(),
    })

    what_changed_today: List[Dict[str, Any]] = []

    if ibov_quote:
        what_changed_today.append({
            "key": "ibov_delta_1d",
            "label": "IBOV Δ 1d",
            "value": ibov_quote.get("change_pct"),
            "unit": "%",
            "extra": {"delta_pts": ibov_quote.get("change_abs"), "delta_pts_unit": "pts"},
            "last_update": ibov_quote.get("last_update"),
            "period_label": "1d"
        })

    if usd_last and usd_prev:
        what_changed_today.append({
            "key": "usdbrl_delta_1d",
            "label": "USD/BRL Δ 1d",
            "value": pct_change(usd_last["value"], usd_prev["value"]),
            "unit": "%",
            "extra": {"delta_brl": usd_last["value"] - usd_prev["value"], "delta_brl_unit": "BRL"},
            "last_update": usd_last["date"] + "T00:00:00Z",
            "period_label": "1d"
        })

    if selic_last and selic_prev:
        what_changed_today.append({
            "key": "selic_last",
            "label": "SELIC (last)",
            "value": selic_last["value"],
            "unit": "% a.a.",
            "extra": {"delta_pp": selic_last["value"] - selic_prev["value"], "delta_pp_unit": "p.p."},
            "last_update": selic_last["date"] + "T00:00:00Z",
            "period_label": "1d"
        })

    if ipca_last and ipca_prev:
        what_changed_today.append({
            "key": "ipca_mm_vs_prev",
            "label": "IPCA (m/m) vs prev",
            "value": ipca_last["value"] - ipca_prev["value"],
            "unit": "p.p.",
            "extra": {"ipca_mm_last": ipca_last["value"], "ipca_mm_prev": ipca_prev["value"], "unit": "%"},
            "last_update": ipca_last["date"] + "T00:00:00Z",
            "period_label": "m/m"
        })

    if unemp_last and unemp_prev:
        what_changed_today.append({
            "key": "unemployment_vs_prev",
            "label": "Desemprego vs prev",
            "value": unemp_last["value"] - unemp_prev["value"],
            "unit": "p.p.",
            "extra": {"unemployment_last": unemp_last["value"], "unemployment_prev": unemp_prev["value"], "unit": "%"},
            "last_update": unemp_last["date"] + "T00:00:00Z",
            "period_label": "m/m"
        })

    if gdp_last and gdp_prev:
        what_changed_today.append({
            "key": "gdp_vs_prev",
            "label": "PIB vs prev",
            "value": gdp_last["value"] - gdp_prev["value"],
            "unit": "raw",
            "extra": {"gdp_last": gdp_last["value"], "gdp_prev": gdp_prev["value"]},
            "last_update": gdp_last["date"] + "T00:00:00Z",
            "period_label": "q/q"
        })

    signals: Dict[str, Any] = {
        "real_rate_approx": {
            "key": "real_rate_approx",
            "label": "Real Rate (approx)",
            "value": real_rate,
            "unit": "p.p.",
            "last_update": iso_now_brapi(),
            "components": {"selic": selic_last["value"] if selic_last else None, "ipca_12m_approx": ipca_12m},
        },
        "inflation_expectations_12m": {
            "key": "inflation_expectations_12m",
            "label": "Inflation expectations (12m) - median",
            "value": expectations["value"] if expectations else None,
            "unit": "%",
            "last_update": expectations["last_update"] if expectations else iso_now_brapi(),
            "source": "BCB Olinda (ExpectativasMercadoInflacao12Meses)",
            "method": "median (prefer smoothed)",
            "cache": exp_bundle["cache"],
        },
        "ibov_vol_20d_annualized": {
            "key": "ibov_vol_20d_annualized",
            "label": "IBOV 20d vol (annualized)",
            "value": ibov_vol,
            "unit": "% a.a.",
            "last_update": iso_now_brapi(),
            "cache": ibov_hist_cache,
        },
        "usdbrl_vol_20d_annualized": {
            "key": "usdbrl_vol_20d_annualized",
            "label": "USD/BRL 20d vol (annualized)",
            "value": usd_vol,
            "unit": "% a.a.",
            "last_update": iso_now_brapi(),
            "cache": usd_hist_cache if usd_hist else usd_cache,
        },
        "unemployment_latest": {
            "key": "unemployment_latest",
            "label": "Unemployment (latest)",
            "value": unemp_last["value"] if unemp_last else None,
            "unit": "%",
            "last_update": (unemp_last["date"] + "T00:00:00Z") if unemp_last else iso_now_brapi(),
        },
        "gdp_latest": {
            "key": "gdp_latest",
            "label": "GDP (latest)",
            "value": gdp_last["value"] if gdp_last else None,
            "unit": "raw",
            "last_update": (gdp_last["date"] + "T00:00:00Z") if gdp_last else iso_now_brapi(),
        },
    }

    # Stale overall if any important provider is stale fallback
    stale = any([
        selic_cache.get("stale"), ipca_cache.get("stale"), usd_cache.get("stale"),
        ibov_quote_cache.get("stale"), exp_bundle["cache"].get("stale")
    ])

    return {
        "top_cards": top_cards,
        "what_changed_today": what_changed_today,
        "signals": signals,
        "meta": {
            "generated_at": iso_now_brapi(),
            "stale": bool(stale),
            "sources": {
                "sgs": {"selic": selic_cache, "ipca": ipca_cache, "usdbrl": usd_cache, "unemployment": unemp_cache, "gdp": gdp_cache},
                "brapi": {"ibov_quote": ibov_quote_cache, "ibov_history": ibov_hist_cache, "usd_history": usd_hist_cache},
                "expectations": exp_bundle["cache"]
            }
        }
    }
