"""
PatentMonitor: Tracks new patent filings in configured technology domains.
Patent filings are one of the most asymmetric intelligence sources available.
"""
import feedparser
import hashlib
import requests
from datetime import datetime, timezone
from typing import List
from loguru import logger
from ingestion.rss_fetcher import RawIntelItem


class PatentMonitor:
    """Monitors patent databases for high-signal new filings."""

    def __init__(self, config: dict):
        self.patent_config = config.get("patent_monitoring", {})
        self.keywords = self.patent_config.get("keywords", [])
        self.enabled = self.patent_config.get("enabled", True)

    def fetch_all(self) -> List[RawIntelItem]:
        if not self.enabled:
            return []

        items = []
        items.extend(self._fetch_google_patents_rss())
        items.extend(self._fetch_arxiv_preprints())
        logger.info(f"[Patents] Fetched {len(items)} patent/research signals")
        return items

    def _fetch_google_patents_rss(self) -> List[RawIntelItem]:
        """Fetch recent patents from Google Patents RSS for each keyword."""
        items = []
        for keyword in self.keywords:
            try:
                encoded = requests.utils.quote(keyword)
                url = f"https://patents.google.com/rss?query={encoded}&before=priority:20260101&num=10"
                feed = feedparser.parse(url)

                for entry in feed.entries[:5]:
                    item_id = hashlib.sha256(entry.get("link", entry.title).encode()).hexdigest()[:16]
                    item = RawIntelItem(
                        id=item_id,
                        title=f"[PATENT] {entry.get('title', 'Untitled')}",
                        url=entry.get("link", ""),
                        source="Google Patents",
                        domain=self._keyword_to_domain(keyword),
                        raw_summary=f"Keyword: {keyword}. {entry.get('summary', '')[:600]}",
                        timestamp=datetime.now(timezone.utc),
                        is_primary_source=True,
                        source_tier="tier1",
                        weight=1.9
                    )
                    items.append(item)
            except Exception as e:
                logger.error(f"[Patents] Google Patents fetch failed for '{keyword}': {e}")

        return items

    def _fetch_arxiv_preprints(self) -> List[RawIntelItem]:
        """Fetch latest arXiv preprints in key domains."""
        items = []
        arxiv_feeds = [
            ("https://rss.arxiv.org/rss/cs.AI", ["ai"]),
            ("https://rss.arxiv.org/rss/quant-ph", ["quantum"]),
            ("https://rss.arxiv.org/rss/q-bio.GN", ["biotech"]),
            ("https://rss.arxiv.org/rss/eess.SY", ["energy"]),
        ]

        for url, domain in arxiv_feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:8]:
                    item_id = hashlib.sha256(entry.get("link", "").encode()).hexdigest()[:16]
                    item = RawIntelItem(
                        id=item_id,
                        title=f"[RESEARCH] {entry.get('title', '')}",
                        url=entry.get("link", ""),
                        source="arXiv",
                        domain=domain,
                        raw_summary=entry.get("summary", "")[:800],
                        timestamp=datetime.now(timezone.utc),
                        is_primary_source=True,
                        source_tier="tier1",
                        weight=1.7
                    )
                    items.append(item)
            except Exception as e:
                logger.error(f"[Patents] arXiv fetch failed for {url}: {e}")

        return items

    def _keyword_to_domain(self, keyword: str) -> List[str]:
        mapping = {
            "artificial intelligence": ["ai"],
            "quantum computing": ["quantum"],
            "gene editing": ["biotech"],
            "fusion energy": ["energy"],
            "autonomous systems": ["tech", "defense"],
            "neural interface": ["biotech", "ai"]
        }
        return mapping.get(keyword, ["tech"])
