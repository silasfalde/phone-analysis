from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


@dataclass
class NotebookcheckResult:
    model: str
    review_url: Optional[str]
    overall_rating_100: Optional[float]
    battery_runtime_hours: Optional[float]


class NotebookcheckScraper:
    """Best-effort scraper for Notebookcheck phone reviews.

    This keeps request volume low and is intentionally conservative.
    """

    def __init__(self, delay_seconds: float = 2.5, timeout_seconds: int = 20) -> None:
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def _sleep(self) -> None:
        time.sleep(self.delay_seconds)

    def _search_url(self, model: str) -> str:
        q = model.strip().replace(" ", "+")
        return f"https://www.notebookcheck.net/index.php?id=103&ns_ajax=1&sQuery={q}"

    def _extract_first_review_url(self, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("a"):
            href = a.get("href")
            if not href:
                continue
            if "Smartphone-Review" in href or "Review" in href:
                if href.startswith("http"):
                    return href
                return "https://www.notebookcheck.net/" + href.lstrip("/")
        return None

    def _extract_overall_rating(self, soup: BeautifulSoup) -> Optional[float]:
        # Notebookcheck often includes percentage-like rating values in review pages.
        text = soup.get_text(" ", strip=True)
        match = re.search(r"(\d{2,3})\s?%", text)
        if not match:
            return None
        value = float(match.group(1))
        if value > 100:
            return None
        return value

    def _extract_battery_runtime_hours(self, soup: BeautifulSoup) -> Optional[float]:
        text = soup.get_text(" ", strip=True)
        # Try common battery runtime pattern such as "12:34 h"
        match = re.search(r"(\d{1,2}):(\d{2})\s?h", text)
        if not match:
            return None
        hours = int(match.group(1))
        mins = int(match.group(2))
        return round(hours + mins / 60.0, 2)

    def fetch_for_model(self, model: str) -> NotebookcheckResult:
        review_url = None
        overall_rating_100 = None
        battery_runtime_hours = None

        try:
            self._sleep()
            search_resp = self.session.get(self._search_url(model), timeout=self.timeout_seconds)
            search_resp.raise_for_status()
            review_url = self._extract_first_review_url(search_resp.text)

            if review_url:
                self._sleep()
                review_resp = self.session.get(review_url, timeout=self.timeout_seconds)
                review_resp.raise_for_status()
                soup = BeautifulSoup(review_resp.text, "html.parser")
                overall_rating_100 = self._extract_overall_rating(soup)
                battery_runtime_hours = self._extract_battery_runtime_hours(soup)
        except Exception:
            # Keep the pipeline resilient; caller can fall back to manual data.
            pass

        return NotebookcheckResult(
            model=model,
            review_url=review_url,
            overall_rating_100=overall_rating_100,
            battery_runtime_hours=battery_runtime_hours,
        )
