"""
SocialSignalFetcher: Monitors Reddit, Hacker News for emerging signals
that precede mainstream coverage by 24-72 hours.
"""
import os
import praw
import requests
import hashlib
from datetime import datetime, timezone
from typing import List
from loguru import logger
from ingestion.rss_fetcher import RawIntelItem


class SocialSignalFetcher:
    """Fetches social intelligence signals."""

    def __init__(self, config: dict):
        self.subreddits = config.get("reddit_subreddits", [])
        self.reddit = self._init_reddit()

    def _init_reddit(self) -> praw.Reddit:
        return praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID", ""),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
            user_agent=os.getenv("REDDIT_USER_AGENT", "EliteIntelAgent/1.0"),
            check_for_async=False
        )

    def fetch_all(self) -> List[RawIntelItem]:
        """Fetch from all configured subreddits."""
        items = []
        items.extend(self._fetch_reddit())
        items.extend(self._fetch_hacker_news())
        logger.info(f"[Social] Fetched {len(items)} social signals")
        return items

    def _fetch_reddit(self) -> List[RawIntelItem]:
        """Fetch top posts from configured subreddits."""
        items = []

        for sub_config in self.subreddits:
            subreddit_name = sub_config.get("subreddit", "")
            domain = sub_config.get("domain", ["general"])
            min_score = sub_config.get("min_score", 100)
            weight = sub_config.get("weight", 1.0)

            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                for post in subreddit.hot(limit=25):
                    if post.score < min_score:
                        continue
                    if post.is_self and len(post.selftext) < 50:
                        continue

                    item_id = hashlib.sha256(post.id.encode()).hexdigest()[:16]
                    velocity_signal = f"Score: {post.score}, Comments: {post.num_comments}, Upvote Ratio: {post.upvote_ratio:.0%}"

                    item = RawIntelItem(
                        id=item_id,
                        title=post.title,
                        url=f"https://reddit.com{post.permalink}",
                        source=f"r/{subreddit_name}",
                        domain=domain,
                        raw_summary=f"{velocity_signal}. {post.selftext[:500] if post.is_self else post.url}",
                        timestamp=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
                        is_primary_source=False,
                        source_tier="tier2",
                        weight=weight
                    )
                    items.append(item)
            except Exception as e:
                logger.error(f"[Social] Reddit r/{subreddit_name} failed: {e}")

        return items

    def _fetch_hacker_news(self) -> List[RawIntelItem]:
        """Fetch top Hacker News stories with high comment velocity."""
        items = []
        try:
            # Get top story IDs
            response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
            story_ids = response.json()[:30]

            for story_id in story_ids:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                story = requests.get(story_url, timeout=5).json()

                if not story:
                    continue

                score = story.get("score", 0)
                num_comments = story.get("descendants", 0)

                # High-signal HN posts: score > 200 or comments > 100
                if score < 200 and num_comments < 100:
                    continue

                item_id = hashlib.sha256(str(story_id).encode()).hexdigest()[:16]
                title = story.get("title", "")
                url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")

                item = RawIntelItem(
                    id=item_id,
                    title=f"[HN] {title}",
                    url=url,
                    source="Hacker News",
                    domain=["tech", "ai"],
                    raw_summary=f"HN Score: {score}, Comments: {num_comments}. Discussion: https://news.ycombinator.com/item?id={story_id}",
                    timestamp=datetime.fromtimestamp(story.get("time", 0), tz=timezone.utc),
                    is_primary_source=False,
                    source_tier="tier2",
                    weight=1.2
                )
                items.append(item)
        except Exception as e:
            logger.error(f"[Social] HackerNews fetch failed: {e}")

        return items
