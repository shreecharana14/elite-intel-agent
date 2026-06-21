"""
RSS Fetcher: Ingests data from 50+ RSS feeds across all configured tiers.
Handles deduplication, rate limiting, and error recovery.
"""
import feedparser
import hashlib
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional
from loguru import logger
from pydantic import BaseModel


class RawIntelItem(BaseModel):
    """A single raw intelligence item from any source."""
    id: str                          # SHA256 hash of URL
    title: str
    url: str
    source: str
    domain: List[str]
    raw_summary: str
    timestamp: datetime
    is_primary_source: bool = False
    source_tier: str = "tier2"
    weight: float = 1.0
    content: Optional[str] = None


class RSSFetcher:
    """
    Fetches and parses RSS feeds from all configured sources.
    Includes deduplication via seen_ids set + SQLite backup.
    """

    def __init__(self, sources_config: dict, seen_ids: Optional[set] = None):
        self.feeds_tier1 = sources_config.get("rss_feeds", {}).get("tier1", [])
        self.feeds_tier2 = sources_config.get("rss_feeds", {}).get("tier2", [])
        self.seen_ids = seen_ids or set()
        self.rate_limit_delay = 1.0  # seconds between requests

    def fetch_all(self, max_age_hours: int = 24) -> List[RawIntelItem]:
        """Fetch from all configured RSS feeds."""
        items = []
        all_feeds = [
            (feed, "tier1") for feed in self.feeds_tier1
        ] + [
            (feed, "tier2") for feed in self.feeds_tier2
        ]

        for feed_config, tier in all_feeds:
            try:
                feed_items = self._fetch_single_feed(feed_config, tier, max_age_hours)
                items.extend(feed_items)
                time.sleep(self.rate_limit_delay)
            except Exception as e:
                logger.error(f"[RSS] Failed to fetch {feed_config.get('name', 'unknown')}: {e}")

        logger.info(f"[RSS] Fetched {len(items)} new items from {len(all_feeds)} feeds")
        return items

    def _fetch_single_feed(self, config: dict, tier: str, max_age_hours: int) -> List[RawIntelItem]:
        """Fetch and parse a single RSS feed."""
        url = config.get("url", "")
        name = config.get("name", "Unknown")
        domain = config.get("domain", ["general"])
        weight = config.get("weight", 1.0)
        is_primary = config.get("is_primary", False)

        logger.debug(f"[RSS] Fetching: {name}")
        feed = feedparser.parse(url)

        items = []
        cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)

        for entry in feed.entries:
            # Generate deterministic ID
            item_id = hashlib.sha256(entry.get("link", entry.get("id", entry.title)).encode()).hexdigest()[:16]

            # Skip if already seen
            if item_id in self.seen_ids:
                continue

            # Skip if too old
            published = entry.get("published_parsed")
            if published:
                pub_timestamp = time.mktime(published)
                if pub_timestamp < cutoff:
                    continue

            # Extract content
            summary = entry.get("summary", "") or entry.get("description", "")
            if hasattr(entry, "content") and entry.content:
                summary = entry.content[0].get("value", summary)

            # Clean HTML
            from bs4 import BeautifulSoup
            clean_summary = BeautifulSoup(summary, "html.parser").get_text(separator=" ", strip=True)[:1000]

            pub_datetime = datetime.fromtimestamp(
                time.mktime(published) if published else time.time(),
                tz=timezone.utc
            )

            item = RawIntelItem(
                id=item_id,
                title=entry.get("title", "No title"),
                url=entry.get("link", url),
                source=name,
                domain=domain,
                raw_summary=clean_summary,
                timestamp=pub_datetime,
                is_primary_source=is_primary,
                source_tier=tier,
                weight=weight
            )
            items.append(item)
            self.seen_ids.add(item_id)

        return items
