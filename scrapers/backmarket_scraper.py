from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class BackMarketListing:
    model: str
    url: Optional[str]
    price_usd: Optional[float]
    seller_rating_5: Optional[float]
    listing_count: Optional[int]


class BackMarketScraper:
    """Playwright-backed BackMarket scraper.

    Notes:
    - BackMarket is JavaScript-heavy and can change DOM frequently.
    - This implementation is best-effort and may require selector tuning over time.
    """

    BASE_URL = "https://www.backmarket.com/en-us"

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless

    def fetch_best_excellent_black_listing(self, model: str) -> BackMarketListing:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            return BackMarketListing(model=model, url=None, price_usd=None, seller_rating_5=None, listing_count=None)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()

            try:
                query = model.strip().replace(" ", "+")
                url = f"{self.BASE_URL}/search?q={query}"
                page.goto(url, wait_until="domcontentloaded", timeout=45000)

                # Attempt to apply condition filter.
                condition_button = page.get_by_text("Excellent", exact=False)
                if condition_button.count() > 0:
                    condition_button.first.click(timeout=3000)

                # Attempt to apply color filter.
                color_button = page.get_by_text("Black", exact=False)
                if color_button.count() > 0:
                    color_button.first.click(timeout=3000)

                page.wait_for_timeout(2500)

                price_values = []
                for locator in page.locator("[data-qa*='price'], [class*='price']").all()[:30]:
                    txt = (locator.text_content() or "").strip().replace(",", "")
                    if "$" not in txt:
                        continue
                    number = "".join(ch for ch in txt if ch.isdigit() or ch == ".")
                    if not number:
                        continue
                    try:
                        price_values.append(float(number))
                    except ValueError:
                        continue

                best_price = min(price_values) if price_values else None

                listing_count = len(price_values) if price_values else None
                browser.close()
                return BackMarketListing(
                    model=model,
                    url=page.url,
                    price_usd=best_price,
                    seller_rating_5=None,
                    listing_count=listing_count,
                )
            except Exception:
                browser.close()
                return BackMarketListing(model=model, url=None, price_usd=None, seller_rating_5=None, listing_count=None)
