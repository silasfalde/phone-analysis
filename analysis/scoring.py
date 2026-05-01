from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Dict, List, Tuple


@dataclass
class ScoringWeights:
    geekbench: float
    price: float
    rating: float
    battery: float


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    txt = str(value).strip()
    if not txt:
        return None
    try:
        return float(txt)
    except ValueError:
        return None


def _safe_minmax(values: List[float | None], invert: bool = False) -> List[float]:
    real = [v for v in values if v is not None]
    if not real:
        return [50.0 for _ in values]

    min_v = min(real)
    max_v = max(real)

    out: List[float] = []
    for v in values:
        if v is None:
            score = 50.0
        elif min_v == max_v:
            score = 100.0
        else:
            score = ((v - min_v) / (max_v - min_v)) * 100.0

        if invert:
            score = 100.0 - score
        out.append(score)
    return out


def compute_scores(rows: List[dict], weights: ScoringWeights) -> List[dict]:
    out = [dict(r) for r in rows]

    geek_values = [_to_float(r.get("geekbench_multi")) for r in out]
    price_values = [_to_float(r.get("backmarket_price_usd")) for r in out]
    rating_values = [_to_float(r.get("rating_100")) for r in out]

    battery_mah_values = [_to_float(r.get("battery_mah")) for r in out]
    battery_runtime_values = [_to_float(r.get("battery_runtime_hours")) for r in out]
    non_null_mah = [v for v in battery_mah_values if v is not None]
    mah_median = median(non_null_mah) if non_null_mah else 5000.0
    battery_composite = [
        (runtime if runtime is not None else 0.0) + (((mah if mah is not None else mah_median) / 1000.0))
        for runtime, mah in zip(battery_runtime_values, battery_mah_values)
    ]

    geek_scores = _safe_minmax(geek_values)
    price_scores = _safe_minmax(price_values, invert=True)
    rating_scores = _safe_minmax(rating_values)
    battery_scores = _safe_minmax(battery_composite)

    for idx, row in enumerate(out):
        row["score_geekbench"] = geek_scores[idx]
        row["score_price"] = price_scores[idx]
        row["score_rating"] = rating_scores[idx]
        row["score_battery"] = battery_scores[idx]
        row["buying_score"] = (
            row["score_geekbench"] * weights.geekbench
            + row["score_price"] * weights.price
            + row["score_rating"] * weights.rating
            + row["score_battery"] * weights.battery
        )

    out.sort(key=lambda r: r["buying_score"], reverse=True)
    for idx, row in enumerate(out, start=1):
        row["rank"] = idx
    return out


def _avg(values: List[float | None]) -> float | None:
    real = [v for v in values if v is not None]
    if not real:
        return None
    return sum(real) / len(real)


def build_brand_analysis(ranked_rows: List[dict]) -> List[dict]:
    by_brand: Dict[str, List[dict]] = {}
    for row in ranked_rows:
        brand = str(row.get("brand") or "Unknown")
        by_brand.setdefault(brand, []).append(row)

    out: List[dict] = []
    for brand, rows in by_brand.items():
        out.append(
            {
                "brand": brand,
                "phone_count": len(rows),
                "avg_buying_score": _avg([_to_float(r.get("buying_score")) for r in rows]),
                "avg_price": _avg([_to_float(r.get("backmarket_price_usd")) for r in rows]),
                "avg_geekbench_multi": _avg([_to_float(r.get("geekbench_multi")) for r in rows]),
                "avg_battery_mah": _avg([_to_float(r.get("battery_mah")) for r in rows]),
            }
        )

    out.sort(key=lambda r: r.get("avg_buying_score") or 0.0, reverse=True)
    return out


def validate_weights(weights_dict: Dict[str, float]) -> Tuple[bool, float]:
    total = sum(weights_dict.values())
    return abs(total - 1.0) < 1e-9, total
