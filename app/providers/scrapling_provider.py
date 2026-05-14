"""
Scrapling tabanlı çok-market fiyat sağlayıcı.
Tesco SSR-rendered sayfalarından veri çeker.
"""
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)

SEARCH_TERMS = [
    "milk", "bread", "eggs", "cheese", "butter",
    "chicken", "beef", "pasta", "rice", "oil",
    "yogurt", "cereal", "biscuits", "juice", "coffee",
]

RETAILERS = {
    "tesco": {
        "url": "https://www.tesco.com/shop/en-GB/search?query={query}&page={page}&count=48",
        "item_selector": 'li[data-auto-available="true"]',
        "name_selector": 'a.P8z7vG_titleLink::text',
        "price_selector": 'p.P8z7vG_priceText::text',
        "unit_selector": 'p.P8z7vG_subtext::text',
        "link_selector": 'a.P8z7vG_titleLink::attr(href)',
    }
    # Diğer marketler test edildikçe buraya eklenir
}


def scrape_retailer(retailer: str, query: str, delay: float = 2.0) -> list[dict]:
    """Tek bir marketin bir kategorisini scrape eder."""
    try:
        from scrapling.fetchers import StealthyFetcher
    except ImportError:
        logger.error("scrapling kurulu degil: pip install 'scrapling[fetchers]'")
        return []

    config = RETAILERS.get(retailer)
    if not config:
        logger.warning(f"Bilinmeyen retailer: {retailer}")
        return []

    results = []
    page = 1
    max_pages = 20  # güvenlik limiti

    while page <= max_pages:
        url = config["url"].format(query=query, page=page)
        try:
            p = StealthyFetcher.fetch(url, headless=True, network_idle=True)
            items = p.css(config["item_selector"])

            if not items:
                break

            for item in items:
                name  = item.css(config["name_selector"]).get()
                price = item.css(config["price_selector"]).get()
                unit  = item.css(config["unit_selector"]).get()
                link  = item.css(config["link_selector"]).get()

                if name and price:
                    # "£1.65" → 1.65
                    price_val = None
                    try:
                        price_val = float(price.replace("£", "").strip())
                    except ValueError:
                        pass

                    results.append({
                        "retailer": retailer,
                        "name": name.strip(),
                        "price_str": price.strip(),
                        "price_gbp": price_val,
                        "unit_price": unit.strip() if unit else None,
                        "url": link,
                        "query": query,
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    })

            page += 1
            time.sleep(delay)

        except Exception as e:
            logger.error(f"{retailer}/{query} sayfa {page} hatasi: {e}")
            break

    return results


def run_full_scrape(
    retailers: list[str] = None,
    queries: list[str] = None,
    output_path: str = "data/scraped_prices.json",
) -> dict:
    """Tüm market + kategorileri scrape edip JSON dosyasına yazar."""
    retailers = retailers or list(RETAILERS.keys())
    queries = queries or SEARCH_TERMS

    all_results = []
    stats = {"started_at": datetime.now(timezone.utc).isoformat(), "counts": {}}

    for retailer in retailers:
        stats["counts"][retailer] = 0
        for query in queries:
            logger.info(f"Scraping: {retailer}/{query}")
            items = scrape_retailer(retailer, query)
            all_results.extend(items)
            stats["counts"][retailer] += len(items)
            time.sleep(3)  # market arası bekleme

    # Kaydet
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"stats": stats, "products": all_results}, f, indent=2, ensure_ascii=False)

    stats["total"] = len(all_results)
    stats["finished_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(f"Scrape tamamlandi: {stats['total']} urun → {output_path}")
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_full_scrape()
