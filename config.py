from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# User requirements
ANDROID_ONLY = True
TARGET_YEARS = [2024, 2025, 2026]
BACKMARKET_COLOR = "black"
BACKMARKET_CONDITION = "excellent"

# Budget is soft, so this is used as a value reference rather than a hard filter.
SOFT_BUDGET_USD = 500

# Requested scoring weights
SCORING_WEIGHTS = {
    "geekbench": 0.35,
    "price": 0.30,
    "rating": 0.20,
    "battery": 0.15,
}

# Input files
PHONES_CSV = DATA_DIR / "phones_curated.csv"
GEEKBENCH_CSV = DATA_DIR / "geekbench_manual.csv"
NOTEBOOKCHECK_CSV = DATA_DIR / "ratings_manual.csv"
BACKMARKET_CSV = DATA_DIR / "backmarket_manual.csv"

# Output files
RANKINGS_CSV = OUTPUT_DIR / "phone_rankings.csv"
BRAND_ANALYSIS_CSV = OUTPUT_DIR / "brand_analysis.csv"
REPORT_HTML = OUTPUT_DIR / "report.html"
