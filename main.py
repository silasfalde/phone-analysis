from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime

import config
from analysis.reporting import build_html_report, save_csv_outputs
from analysis.scoring import ScoringWeights, build_brand_analysis, compute_scores, validate_weights
from scrapers.backmarket_scraper import BackMarketScraper
from scrapers.notebookcheck_scraper import NotebookcheckScraper


def _read_csv_rows(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _index_by_brand_model(rows: list[dict]) -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (str(row.get("brand") or ""), str(row.get("model") or ""))
        out[key] = row
    return out


def _as_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _load_base_data() -> list[dict]:
    phones = _read_csv_rows(str(config.PHONES_CSV))
    geek = _index_by_brand_model(_read_csv_rows(str(config.GEEKBENCH_CSV)))
    rating = _index_by_brand_model(_read_csv_rows(str(config.NOTEBOOKCHECK_CSV)))
    backmarket = _index_by_brand_model(_read_csv_rows(str(config.BACKMARKET_CSV)))

    out = []
    for p in phones:
        key = (str(p.get("brand") or ""), str(p.get("model") or ""))
        merged = dict(p)
        merged.update(geek.get(key, {}))
        merged.update(rating.get(key, {}))
        merged.update(backmarket.get(key, {}))

        if config.ANDROID_ONLY and str(merged.get("os_family", "")).lower() != "android":
            continue

        rel_year = _as_int(merged.get("release_year"))
        if rel_year is not None and rel_year not in config.TARGET_YEARS:
            continue

        out.append(merged)

    return out


def _apply_live_backmarket(rows: list[dict], headless: bool = True) -> list[dict]:
    scraper = BackMarketScraper(headless=headless)
    out = []
    for row in rows:
        result = scraper.fetch_best_excellent_black_listing(row["model"])
        updated = dict(row)
        updated["backmarket_price_usd"] = result.price_usd
        updated["backmarket_listing_count"] = result.listing_count
        updated["backmarket_url"] = result.url
        out.append(updated)
    return out


def _apply_live_notebookcheck(rows: list[dict]) -> list[dict]:
    scraper = NotebookcheckScraper()
    out = []
    for row in rows:
        result = scraper.fetch_for_model(row["model"])
        updated = dict(row)
        updated["rating_100"] = result.overall_rating_100
        updated["battery_runtime_hours"] = result.battery_runtime_hours
        updated["notebookcheck_url"] = result.review_url
        out.append(updated)
    return out


def run_pipeline(live_backmarket: bool, live_notebookcheck: bool, headless: bool) -> None:
    valid, total = validate_weights(config.SCORING_WEIGHTS)
    if not valid:
        raise ValueError(f"Scoring weights must sum to 1.0; got {total}")

    df = _load_base_data()

    if live_notebookcheck:
        df = _apply_live_notebookcheck(df)

    if live_backmarket:
        df = _apply_live_backmarket(df, headless=headless)

    weights = ScoringWeights(
        geekbench=config.SCORING_WEIGHTS["geekbench"],
        price=config.SCORING_WEIGHTS["price"],
        rating=config.SCORING_WEIGHTS["rating"],
        battery=config.SCORING_WEIGHTS["battery"],
    )

    ranked = compute_scores(df, weights)
    brand = build_brand_analysis(ranked)

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).isoformat()
    for row in ranked:
        row["analysis_generated_at"] = ts

    save_csv_outputs(ranked, brand, config.RANKINGS_CSV, config.BRAND_ANALYSIS_CSV)
    build_html_report(ranked, brand, config.REPORT_HTML, top_n=10)

    cols = [
        "rank",
        "brand",
        "model",
        "buying_score",
        "backmarket_price_usd",
        "geekbench_multi",
        "rating_100",
        "battery_mah",
        "battery_runtime_hours",
    ]

    def _fmt(value: object) -> str:
        if value is None:
            return "N/A"
        return str(value)

    print("\nTop 10 phones by buying score:\n")
    for row in ranked[:10]:
        print(" | ".join(_fmt(row.get(c)) for c in cols))

    print("\nBrand analysis:\n")
    for row in brand:
        print(" | ".join(_fmt(row.get(c)) for c in ["brand", "phone_count", "avg_buying_score", "avg_price", "avg_geekbench_multi", "avg_battery_mah"]))

    print(f"\nSaved: {config.RANKINGS_CSV}")
    print(f"Saved: {config.BRAND_ANALYSIS_CSV}")
    print(f"Saved: {config.REPORT_HTML}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Android phone buying analysis with optional live scraping")
    parser.add_argument("--live-backmarket", action="store_true", help="Use live BackMarket scraping instead of manual CSV data")
    parser.add_argument("--live-notebookcheck", action="store_true", help="Use live Notebookcheck scraping instead of manual CSV data")
    parser.add_argument("--show-browser", action="store_true", help="Run browser in visible mode for debugging BackMarket scraping")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        live_backmarket=args.live_backmarket,
        live_notebookcheck=args.live_notebookcheck,
        headless=not args.show_browser,
    )
