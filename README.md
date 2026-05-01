# Phone Analysis — Android Buying Assistant

This repository provides a small pipeline to help choose an Android phone to buy based on combined signals: review ratings, Geekbench performance, and BackMarket pricing. It's designed to prioritize long-term use (6–10 years) with emphasis on CPU performance and battery life, and it includes live scraping hooks plus offline seed data.

**Notable features**
- Scoring formula combining Geekbench, price, rating, and battery (weights configurable)
- Seeded dataset so you can run an analysis immediately (no scraping required)
- Optional live scraping for Notebookcheck and BackMarket (Playwright)
- HTML and CSV outputs with top-ranked phones and brand-level analysis

**Repository layout**
- `main.py` — Orchestrator script to run the pipeline
- `config.py` — Scoring weights, filters, input/output paths
- `scrapers/` — `notebookcheck_scraper.py` and `backmarket_scraper.py` (live scraping)
- `analysis/` — `scoring.py` and `reporting.py` (scoring and report generation)
- `data/` — Seed CSVs: `phones_curated.csv`, `geekbench_manual.csv`, `ratings_manual.csv`, `backmarket_manual.csv`
- `output/` — Generated CSV and HTML outputs after a run
- `requirements.txt` — Python dependencies

Quickstart
----------
1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the offline/seeded analysis (uses CSVs in `data/`):

```bash
python main.py
```

3. Optional: run with live scraping (requires Playwright browser support). Run Playwright install once if you plan to use it:

```bash
# Install Playwright browsers (only needed once)
python -m playwright install

# Run pipeline with live scraping (may be slower and brittle)
python main.py --live-backmarket --live-notebookcheck
```

Outputs
-------
- `output/phone_rankings.csv` — Ranked phones and per-phone score breakdown
- `output/brand_analysis.csv` — Brand-level aggregation
- `output/report.html` — Human-readable report with top results

Configuration
-------------
Edit `config.py` to change:
- `SCORING_WEIGHTS` (default: geekbench 35%, price 30%, rating 20%, battery 15%)
- `TARGET_YEARS` to adjust the release-year filter
- `BACKMARKET_COLOR` and `BACKMARKET_CONDITION` to change BackMarket filters

Legal & ethical notes (important)
---------------------------------
- Live scraping can violate websites' Terms of Service. The included scrapers are "best-effort" examples and should be used responsibly.
- BackMarket and Geekbench may block automated access or change markup frequently. If you want robust/production data, consider using official APIs (if available) or licensed datasets.
- Always respect robots.txt and rate limits; avoid high-frequency scraping.

Data provenance and limitations
------------------------------
- Seed data in `data/` is manually curated for demonstration and may not be exhaustive or up to date.
- Battery runtime and rating values are approximate and sourced from review snapshots. Actual battery longevity depends on use and software updates.
- The scoring formula is a heuristic to balance performance, price, and battery for long-term use; tweak weights in `config.py` to match your priorities.

Next steps / Enhancements
-------------------------
- Add LineageOS compatibility signal to the score (devices known to be supported get a longevity bonus).
- Improve BackMarket scraping robustness (selectors, pagination, proxies) or replace with a manual price scrape step if needed.
- Add repairability (iFixit) and software update policy indicators to better estimate 6–10 year longevity.
- Persist historical prices for trend analysis.

Support / Contact
-----------------
If you want me to adapt the scoring weights, add LineageOS checks, or harden live scrapers, tell me which feature to prioritize and I will implement it.
