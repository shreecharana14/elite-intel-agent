#!/usr/bin/env python3
"""
Elite Intel System — Minimal Version with Gemini 2.0 Flash (FREE)
Runs every 30 minutes via cron.

Flow:
  1. Fetch from RSS feeds, financial APIs, social signals
  2. Deduplicate and score (pure Python)
  3. Take top 5-7 items
  4. Send to Gemini: "Write an elite brief"
  5. Send brief to Telegram
"""

import os
import sys
import json
import sqlite3
import time
import hashlib
from datetime import datetime, timezone
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv(".env.gemini")

import logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

import feedparser
import requests
from telegram import Bot

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from minimal.scoring_rules import RawIntelItem, batch_score
from minimal.llm_providers import get_provider

DB_PATH = os.getenv("DB_PATH", "./data/intel.db")
MIN_SCORE = int(os.getenv("MIN_SIGNAL_SCORE", "70"))
MAX_ITEMS = int(os.getenv("MAX_BRIEF_ITEMS", "7"))

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seen_items (
            item_id TEXT PRIMARY KEY,
            title TEXT,
            url TEXT,
            seen_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS briefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            item_count INTEGER,
            provider TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_seen_ids() -> set:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    rows = cursor.execute("SELECT item_id FROM seen_items").fetchall()
    conn.close()
    return {row[0] for row in rows}

def mark_seen(item_id: str, title: str, url: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO seen_items (item_id, title, url) VALUES (?, ?, ?)",
        (item_id, title, url)
    )
    conn.commit()
    conn.close()

def fetch_rss_feeds() -> List[RawIntelItem]:
    items = []
    seen_ids = get_seen_ids()
    feeds = [
        ("https://feeds.reuters.com/reuters/technologyNews", "Reuters", ["tech"]),
        ("https://feeds.bloomberg.com/technology/news.rss", "Bloomberg", ["tech", "finance"]),
        ("https://rss.arxiv.org/rss/cs.AI", "arXiv", ["ai"]),
        ("https://news.ycombinator.com/rss", "HN", ["tech"]),
        ("https://www.ft.com/rss/home", "FT", ["finance", "geopolitics"]),
    ]
    for feed_url, source, domains in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                url = entry.get("link", feed_url)
                item_id = hashlib.sha256(url.encode()).hexdigest()[:16]
                if item_id in seen_ids:
                    continue
                summary = entry.get("summary", "") or entry.get("description", "")
                from bs4 import BeautifulSoup
                summary = BeautifulSoup(summary, "html.parser").get_text()[:500]
                items.append(RawIntelItem(
                    title=entry.get("title", ""),
                    url=url,
                    source=source,
                    domain=domains,
                    summary=summary,
                    is_primary=False
                ))
        except Exception as e:
            logger.warning(f"Feed {source} failed: {e}")
    logger.info(f"📡 Fetched {len(items)} items from RSS feeds")
    return items

def fetch_sec_filings() -> List[RawIntelItem]:
    items = []
    try:
        feed = feedparser.parse("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&dateb=&owner=include&count=20&output=atom")
        for entry in feed.entries[:5]:
            items.append(RawIntelItem(
                title=f"[SEC 4-FORM] {entry.get('title', '')}",
                url=entry.get("link", ""),
                source="SEC EDGAR",
                domain=["finance"],
                summary=entry.get("summary", "")[:500],
                is_primary=True
            ))
    except Exception as e:
        logger.warning(f"SEC fetch failed: {e}")
    logger.info(f"💰 Fetched {len(items)} SEC filings")
    return items

def fetch_hacker_news_top() -> List[RawIntelItem]:
    items = []
    try:
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=5)
        story_ids = response.json()[:10]
        for story_id in story_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            story = requests.get(story_url, timeout=3).json()
            if not story:
                continue
            score = story.get("score", 0)
            comments = story.get("descendants", 0)
            if score >= 200 or comments >= 50:
                title = story.get("title", "")
                url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                items.append(RawIntelItem(
                    title=f"[HN] {title}",
                    url=url,
                    source="Hacker News",
                    domain=["tech"],
                    summary=f"Score: {score}, Comments: {comments}",
                    is_primary=False
                ))
    except Exception as e:
        logger.warning(f"HN fetch failed: {e}")
    logger.info(f"📰 Fetched {len(items)} HN stories")
    return items

def run_intelligence_cycle():
    logger.info("=" * 60)
    logger.info("🚀 INTELLIGENCE CYCLE STARTING (Gemini 2.0 Flash - FREE)")
    logger.info("=" * 60)
    logger.info("Step 1: Fetching data...")
    cycle_start = time.time()
    
    all_items = []
    all_items.extend(fetch_rss_feeds())
    all_items.extend(fetch_sec_filings())
    all_items.extend(fetch_hacker_news_top())
    logger.info(f"✅ Total items fetched: {len(all_items)}")
    
    if not all_items:
        logger.warning("No items found. Exiting.")
        return
    
    logger.info("Step 2: Scoring items...")
    scored = batch_score(all_items)
    elite = [s for s in scored if s["composite_score"] >= MIN_SCORE]
    elite = elite[:MAX_ITEMS]
    logger.info(f"✅ Elite items (score >= {MIN_SCORE}): {len(elite)}")
    
    if not elite:
        logger.warning("No elite items. Exiting.")
        return
    
    logger.info("Step 3: Calling Gemini 2.0 Flash for synthesis...")
    provider = get_provider(
        provider_name=os.getenv("LLM_PROVIDER", "gemini"),
        fallback_provider=os.getenv("FALLBACK_PROVIDER", "claude")
    )
    brief = provider.synthesize(elite)
    
    if not brief:
        logger.error("Brief generation failed.")
        return
    
    logger.info("Step 4: Saving and sending...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO briefs (content, item_count, provider) VALUES (?, ?, ?)",
        (brief, len(elite), os.getenv("LLM_PROVIDER", "gemini"))
    )
    conn.commit()
    conn.close()
    
    send_to_telegram(brief)
    
    for item in elite:
        mark_seen(
            hashlib.sha256(item["url"].encode()).hexdigest()[:16],
            item["title"],
            item["url"]
        )
    
    elapsed = time.time() - cycle_start
    logger.info("=" * 60)
    logger.info(f"✅ CYCLE COMPLETE in {elapsed:.1f}s")
    logger.info("=" * 60)

def send_to_telegram(brief: str):
    try:
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        brief = brief[:4000]
        bot.send_message(chat_id=chat_id, text=brief, parse_mode="Markdown")
        logger.info("✅ Brief sent to Telegram")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")

if __name__ == "__main__":
    init_db()
    run_intelligence_cycle()
