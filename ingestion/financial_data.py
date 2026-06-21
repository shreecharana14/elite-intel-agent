"""
FinancialDataFetcher: Monitors insider trading, institutional filings,
VC funding rounds, and market anomalies.
"""
import os
import requests
from datetime import datetime, timezone
from typing import List, Dict
from loguru import logger
from ingestion.rss_fetcher import RawIntelItem
import hashlib


class FinancialDataFetcher:
    """Fetches high-signal financial intelligence."""

    def __init__(self, config: dict):
        self.config = config.get("financial_signals", {})
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.polygon_key = os.getenv("POLYGON_API_KEY", "")

    def fetch_all(self) -> List[RawIntelItem]:
        """Fetch all financial signals."""
        items = []

        if self.config.get("insider_trading", {}).get("enabled", False):
            items.extend(self._fetch_insider_trades())

        if self.config.get("institutional_filings", {}).get("enabled", False):
            items.extend(self._fetch_institutional_filings())

        if self.config.get("vc_funding", {}).get("enabled", False):
            items.extend(self._fetch_vc_funding())

        logger.info(f"[Financial] Fetched {len(items)} financial signals")
        return items

    def _fetch_insider_trades(self) -> List[RawIntelItem]:
        """Monitor SEC Form 4 insider trading filings."""
        items = []
        threshold = self.config.get("insider_trading", {}).get("threshold_value", 1_000_000)

        try:
            import feedparser
            url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&dateb=&owner=include&count=40&output=atom"
            feed = feedparser.parse(url)

            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")

                item_id = hashlib.sha256(link.encode()).hexdigest()[:16]

                item = RawIntelItem(
                    id=item_id,
                    title=f"[INSIDER TRADE] {title}",
                    url=link,
                    source="SEC EDGAR Form 4",
                    domain=["finance"],
                    raw_summary=summary[:800],
                    timestamp=datetime.now(timezone.utc),
                    is_primary_source=True,
                    source_tier="tier1",
                    weight=2.0
                )
                items.append(item)
        except Exception as e:
            logger.error(f"[Financial] Insider trade fetch failed: {e}")

        return items

    def _fetch_institutional_filings(self) -> List[RawIntelItem]:
        """Monitor 13F, SC 13G, SC 13D institutional filings."""
        items = []
        filing_types = self.config.get("institutional_filings", {}).get("filing_types", ["13F"])

        try:
            import feedparser
            for filing_type in filing_types:
                url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type={filing_type}&dateb=&owner=include&count=20&output=atom"
                feed = feedparser.parse(url)

                for entry in feed.entries[:10]:
                    item_id = hashlib.sha256(entry.get("link", "").encode()).hexdigest()[:16]
                    item = RawIntelItem(
                        id=item_id,
                        title=f"[{filing_type} FILING] {entry.get('title', '')}",
                        url=entry.get("link", ""),
                        source=f"SEC EDGAR {filing_type}",
                        domain=["finance"],
                        raw_summary=entry.get("summary", "")[:800],
                        timestamp=datetime.now(timezone.utc),
                        is_primary_source=True,
                        source_tier="tier1",
                        weight=1.8
                    )
                    items.append(item)
        except Exception as e:
            logger.error(f"[Financial] Institutional filing fetch failed: {e}")

        return items

    def _fetch_vc_funding(self) -> List[RawIntelItem]:
        """Monitor VC funding rounds above threshold."""
        items = []
        sources = self.config.get("vc_funding", {}).get("sources", [])
        min_amount = self.config.get("vc_funding", {}).get("min_amount_millions", 50)

        try:
            import feedparser
            for source_url in sources:
                feed = feedparser.parse(source_url)
                for entry in feed.entries[:15]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")

                    # Simple heuristic: check if dollar amount is mentioned
                    has_large_amount = any(
                        indicator in title.lower() or indicator in summary.lower()
                        for indicator in ["$100m", "$500m", "$1b", "billion", "unicorn", "series c", "series d", "ipo"]
                    )

                    if has_large_amount:
                        item_id = hashlib.sha256(entry.get("link", title).encode()).hexdigest()[:16]
                        item = RawIntelItem(
                            id=item_id,
                            title=f"[VC/FUNDING] {title}",
                            url=entry.get("link", ""),
                            source="VC Funding Monitor",
                            domain=["finance", "tech"],
                            raw_summary=summary[:800],
                            timestamp=datetime.now(timezone.utc),
                            is_primary_source=False,
                            source_tier="tier2",
                            weight=1.3
                        )
                        items.append(item)
        except Exception as e:
            logger.error(f"[Financial] VC funding fetch failed: {e}")

        return items
