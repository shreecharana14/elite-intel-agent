"""
RegulatoryMonitor: Tracks regulatory filings and policy changes.
Regulatory shifts are the highest-asymmetry signals available to the public.
"""
import feedparser
import hashlib
from datetime import datetime, timezone
from typing import List
from loguru import logger
from ingestion.rss_fetcher import RawIntelItem


class RegulatoryMonitor:
    """Monitors regulatory bodies for high-signal policy changes."""

    def __init__(self, config: dict):
        self.reg_config = config.get("regulatory_monitoring", {})
        self.enabled = self.reg_config.get("enabled", True)
        self.sources = self.reg_config.get("sources", [])

    def fetch_all(self) -> List[RawIntelItem]:
        if not self.enabled:
            return []

        items = []
        for source in self.sources:
            try:
                feed_items = self._fetch_regulatory_feed(source)
                items.extend(feed_items)
            except Exception as e:
                logger.error(f"[Regulatory] Failed to fetch {source.get('name')}: {e}")

        logger.info(f"[Regulatory] Fetched {len(items)} regulatory signals")
        return items

    def _fetch_regulatory_feed(self, source: dict) -> List[RawIntelItem]:
        name = source.get("name", "Unknown Regulatory")
        url = source.get("url", "")
        domain = source.get("domain", ["regulation"])

        feed = feedparser.parse(url)
        items = []

        for entry in feed.entries[:10]:
            item_id = hashlib.sha256(entry.get("link", entry.get("id", "")).encode()).hexdigest()[:16]
            item = RawIntelItem(
                id=item_id,
                title=f"[REGULATORY] {entry.get('title', '')}",
                url=entry.get("link", url),
                source=name,
                domain=domain,
                raw_summary=entry.get("summary", "")[:800],
                timestamp=datetime.now(timezone.utc),
                is_primary_source=True,
                source_tier="tier1",
                weight=2.0  # Regulatory is highest weight
            )
            items.append(item)

        return items
