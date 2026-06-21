"""
Scoring Rules: Pure Python logic for signal scoring.
No LLM calls. Deterministic. Fast.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List

# ============ SCORING CONFIGURATION ============

NOVELTY_CONFIG = {
    "primary_source_boost": 2.0,
    "tier1_boost": 1.5,
    "tier2_baseline": 1.0,
    "mainstream_penalty": 0.3,
}

VELOCITY_CONFIG = {
    "thresholds": {
        10: 10.0,
        5: 7.0,
        2: 4.0,
        0: 2.0,
    }
}

ACTIONABILITY_KEYWORDS = {
    "high": [
        "acquisition", "merger", "ipo", "patent approved", "regulation passed",
        "executive arrested", "ceo fired", "breach", "vulnerability", "exploit",
        "breakthrough", "approval", "sanction", "ban", "ruling", "verdict",
    ],
    "medium": [
        "hiring", "layoff", "investment", "partnership", "trial", "study",
        "research", "acquisition talks", "considering", "exploring", "beta",
    ],
    "low": [
        "announcement", "report", "opinion", "analysis", "speculation",
    ]
}

ASYMMETRY_SOURCES = {
    "high": [
        "sec.gov", "arxiv.org", "patents.google.com", "epo.org",
        "biorxiv.org", "github.com", "eurekalert.org",
    ],
    "low": [
        "cnn.com", "bbc.com", "nytimes.com", "theguardian.com",
        "reddit.com", "twitter.com", "facebook.com",
    ]
}

class RawIntelItem:
    def __init__(self, **kwargs):
        self.title = kwargs.get("title", "")
        self.url = kwargs.get("url", "")
        self.source = kwargs.get("source", "")
        self.domain = kwargs.get("domain", [])
        self.summary = kwargs.get("summary", "")
        self.timestamp = kwargs.get("timestamp", datetime.now(timezone.utc))
        self.is_primary = kwargs.get("is_primary", False)

def score_item(item: RawIntelItem, velocity_count: int = 0) -> Dict:
    text = f"{item.title} {item.summary}".lower()
    url = item.url.lower()
    
    novelty = _score_novelty(item, url)
    velocity = _score_velocity(velocity_count)
    source_auth = _score_source_authority(item)
    actionability = _score_actionability(text)
    cross_domain = _score_cross_domain(item.domain)
    asymmetry = _score_asymmetry(url, text)
    
    weights = {
        "novelty": 0.25,
        "velocity": 0.20,
        "source_authority": 0.15,
        "actionability": 0.20,
        "cross_domain": 0.10,
        "asymmetry": 0.10,
    }
    
    composite = (
        novelty * weights["novelty"] +
        velocity * weights["velocity"] +
        source_auth * weights["source_authority"] +
        actionability * weights["actionability"] +
        cross_domain * weights["cross_domain"] +
        asymmetry * weights["asymmetry"]
    ) * 10
    
    return {
        "title": item.title,
        "url": item.url,
        "source": item.source,
        "domain": item.domain,
        "summary": item.summary[:300],
        "composite_score": round(min(100, max(0, composite)), 1),
        "score_breakdown": {
            "novelty": round(novelty, 1),
            "velocity": round(velocity, 1),
            "source_authority": round(source_auth, 1),
            "actionability": round(actionability, 1),
            "cross_domain": round(cross_domain, 1),
            "asymmetry": round(asymmetry, 1),
        }
    }

def _score_novelty(item: RawIntelItem, url: str) -> float:
    if item.is_primary:
        return 9.0
    if any(t in url for t in ["reuters.com", "bloomberg.com", "arxiv.org", "sec.gov"]):
        return 7.0
    if any(t in url for t in ["techcrunch.com", "news.ycombinator.com"]):
        return 5.0
    if any(t in url for t in ASYMMETRY_SOURCES["low"]):
        return 2.0
    return 4.0

def _score_velocity(count: int) -> float:
    thresholds = VELOCITY_CONFIG["thresholds"]
    for threshold in sorted(thresholds.keys(), reverse=True):
        if count >= threshold:
            return thresholds[threshold]
    return 2.0

def _score_source_authority(item: RawIntelItem) -> float:
    if item.is_primary:
        return 10.0
    if "tier1" in str(item.domain).lower():
        return 7.0
    return 4.0

def _score_actionability(text: str) -> float:
    high = sum(1 for kw in ACTIONABILITY_KEYWORDS["high"] if kw in text)
    medium = sum(1 for kw in ACTIONABILITY_KEYWORDS["medium"] if kw in text)
    score = min(10, high * 3.0 + medium * 1.5)
    return max(1.0, score)

def _score_cross_domain(domains: List[str]) -> float:
    if len(domains) >= 3:
        return 10.0
    elif len(domains) == 2:
        return 6.0
    return 2.0

def _score_asymmetry(url: str, text: str) -> float:
    if any(mainstream in url for mainstream in ASYMMETRY_SOURCES["low"]):
        return 2.0
    if any(source in url for source in ASYMMETRY_SOURCES["high"]):
        return 9.5
    return 6.0

def batch_score(items: List[RawIntelItem]) -> List[Dict]:
    scored = [score_item(item) for item in items]
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored
