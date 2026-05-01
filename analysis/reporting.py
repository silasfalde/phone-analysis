from __future__ import annotations

import csv
from pathlib import Path

from jinja2 import Template


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_csv_outputs(ranked_df: list[dict], brand_df: list[dict], rankings_csv: Path, brand_csv: Path) -> None:
    _write_csv(rankings_csv, ranked_df)
    _write_csv(brand_csv, brand_df)


def build_html_report(ranked_df: list[dict], brand_df: list[dict], output_path: Path, top_n: int = 10) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    top_rows = ranked_df[:top_n]

    template = Template(
        """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Android Phone Buying Analysis</title>
  <style>
    :root {
      --bg: #f4f7f8;
      --card: #ffffff;
      --text: #0f1f24;
      --muted: #4b6169;
      --accent: #0b7a75;
      --accent-soft: #d8f1ef;
      --line: #d3dee2;
    }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background: radial-gradient(circle at 10% 10%, #dff5ef, var(--bg));
      color: var(--text);
      padding: 24px;
    }
    .wrap {
      max-width: 1200px;
      margin: 0 auto;
      display: grid;
      gap: 16px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 10px 30px rgba(8, 25, 33, 0.05);
    }
    h1, h2 {
      margin: 0 0 10px;
      letter-spacing: -0.02em;
    }
    p {
      margin: 0;
      color: var(--muted);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 14px;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      text-align: left;
      padding: 8px;
      vertical-align: top;
    }
    th {
      background: var(--accent-soft);
      color: var(--text);
      font-weight: 700;
      position: sticky;
      top: 0;
    }
    .score {
      font-weight: 700;
      color: var(--accent);
    }
    .meta {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
      margin-top: 8px;
    }
    .chip {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      width: fit-content;
      background: #f9fcfd;
      font-size: 12px;
      color: var(--muted);
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"card\">
      <h1>Android Phone Buying Analysis</h1>
      <p>Ranking optimized for long-term LineageOS usage with emphasis on performance, battery, and value.</p>
      <div class=\"meta\">
        <div class=\"chip\">Weights: Geekbench 35%, Price 30%, Rating 20%, Battery 15%</div>
        <div class=\"chip\">BackMarket filters: Excellent condition, Black color</div>
        <div class=\"chip\">Scope: Android phones (2024-2026 pool)</div>
      </div>
    </section>

    <section class=\"card\">
      <h2>Top {{ top_n }} Phones By Buying Score</h2>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Brand</th>
            <th>Model</th>
            <th>Buying Score</th>
            <th>BackMarket Price (USD)</th>
            <th>Geekbench Multi</th>
            <th>Rating / 100</th>
            <th>Battery mAh</th>
            <th>Battery Runtime (hrs)</th>
          </tr>
        </thead>
        <tbody>
          {% for row in top_rows %}
          <tr>
            <td>{{ row.rank }}</td>
            <td>{{ row.brand }}</td>
            <td>{{ row.model }}</td>
            <td class=\"score\">{{ '%.2f'|format(row.buying_score) }}</td>
            <td>{{ row.backmarket_price_usd if row.backmarket_price_usd is not none else 'N/A' }}</td>
            <td>{{ row.geekbench_multi if row.geekbench_multi is not none else 'N/A' }}</td>
            <td>{{ row.rating_100 if row.rating_100 is not none else 'N/A' }}</td>
            <td>{{ row.battery_mah if row.battery_mah is not none else 'N/A' }}</td>
            <td>{{ row.battery_runtime_hours if row.battery_runtime_hours is not none else 'N/A' }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>

    <section class=\"card\">
      <h2>Brand-Level Analysis</h2>
      <table>
        <thead>
          <tr>
            <th>Brand</th>
            <th>Phone Count</th>
            <th>Average Buying Score</th>
            <th>Average Price</th>
            <th>Average Geekbench Multi</th>
            <th>Average Battery mAh</th>
          </tr>
        </thead>
        <tbody>
          {% for row in brand_rows %}
          <tr>
            <td>{{ row.brand }}</td>
            <td>{{ row.phone_count }}</td>
            <td class=\"score\">{{ '%.2f'|format(row.avg_buying_score) }}</td>
            <td>{{ '%.2f'|format(row.avg_price) if row.avg_price is not none else 'N/A' }}</td>
            <td>{{ '%.2f'|format(row.avg_geekbench_multi) if row.avg_geekbench_multi is not none else 'N/A' }}</td>
            <td>{{ '%.2f'|format(row.avg_battery_mah) if row.avg_battery_mah is not none else 'N/A' }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
  </div>
</body>
</html>
        """
    )

    html = template.render(top_n=top_n, top_rows=top_rows, brand_rows=brand_df)
    output_path.write_text(html, encoding="utf-8")
