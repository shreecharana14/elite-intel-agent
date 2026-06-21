"""
SignalScorer: ML-powered scoring engine that evaluates each intelligence item
across 6 dimensions. Weights are updated by the self-learning loop.
"""
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional
from loguru import logger
from ingestion.rss_fetcher import RawIntelItem


class SignalScorer:
    """
    Scores each raw intelligence item on 6 dimensions:
    Novelty, Velocity, Source Authority, Actionability, Cross-Domain, Asymmetry.
    """

    MAINSTREAM_DOMAINS = [
        "cnn.com", "bbc.com", "nytimes.com", "theguardian.com",
        "foxnews.com", "msn.com", "yahoo.com", "huffpost.com"
    ]

    ACTIONABILITY_HIGH = [
        "acquisition", "merger", "patent", "filing", "approval", "ban",
        "launch", "breakthrough", "arrested", "indicted", "sanctioned",
        "regulation", "ruling", "verdict", "shutdown", "recall"
    ]

    ACTIONABILITY_MEDIUM = [
        "partnership", "investment", "research", "study", "report",
        "trial", "pilot", "hiring", "layoff", "expansion"
    ]

    def __init__(self, weights: Dict[str, float], domain_biases: Dict[str, float]):
        self.weights = weights
        self.domain_biases = domain_biases

    def score_item(self, item: RawIntelItem, velocity_count: int = 0) -> Dict:
        """Score a single intelligence item. Returns full scoring breakdown."""

        text = f"{item.title} {item.raw_summary}".lower()
        url = item.url.lower()

        # 1. Novelty Score
        novelty = self._score_novelty(item)

        # 2. Velocity Score
        velocity = self._score_velocity(velocity_count)

        # 3. Source Authority Score
        source_auth = self._score_source_authority(item)

        # 4. Actionability Score
        actionability = self._score_actionability(text)

        # 5. Cross-Domain Score
        cross_domain = self._score_cross_domain(item.domain)

        # 6. Asymmetry Score
        asymmetry = self._score_asymmetry(url, text)

        # Weighted composite score (0-100)
        w = self.weights
        raw_score = (
            novelty * w.get("novelty", 0.25) +
            velocity * w.get("velocity", 0.20) +
            source_auth * w.get("source_authority", 0.15) +
            actionability * w.get("actionability", 0.20) +
            cross_domain * w.get("cross_domain", 0.10) +
            asymmetry * w.get("asymmetry", 0.10)
        ) * 10  # Scale to 0-100

        # Apply domain bias (user preference)
        domain_multiplier = max(
            self.domain_biases.get(d, 1.0) for d in item.domain
        )
        final_score = min(100, raw_score * domain_multiplier * item.weight)

        return {
            "id": item.id,
            "title": item.title,
            "url": item.url,
            "source": item.source,
            "domain": item.domain,
            "raw_summary": item.raw_summary,
            "timestamp": item.timestamp.isoformat(),
            "is_primary_source": item.is_primary_source,
            "composite_score": round(final_score, 1),
            "score_breakdown": {
                "novelty": round(novelty, 1),
                "velocity": round(velocity, 1),
                "source_authority": round(source_auth, 1),
                "actionability": round(actionability, 1),
                "cross_domain": round(cross_domain, 1),
                "asymmetry": round(asymmetry, 1)
            },
            "rationale": self._generate_rationale(item, novelty, velocity, source_auth, actionability)
        }

    def _score_novelty(self, item: RawIntelItem) -> float:
        # Primary sources are inherently more novel
        if item.is_primary_source:
            return 8.5
        if item.source_tier == "tier1":
            return 6.0
        return 4.0

    def _score_velocity(self, count: int) -> float:
        if count >= 10:
            return 10.0
        elif count >= 5:
            return 7.0
        elif count >= 2:
            return 4.0
        return 2.0

    def _score_source_authority(self, item: RawIntelItem) -> float:
        if item.is_primary_source:
            return 10.0
        if item.source_tier == "tier1":
            return 7.0
        return 4.0

    def _score_actionability(self, text: str) -> float:
        high_count = sum(1 for kw in self.ACTIONABILITY_HIGH if kw in text)
        medium_count = sum(1 for kw in self.ACTIONABILITY_MEDIUM if kw in text)
        score = min(10, high_count * 3.0 + medium_count * 1.5)
        return max(1.0, score)

    def _score_cross_domain(self, domains: List[str]) -> float:
        if len(domains) >= 3:
            return 10.0
        elif len(domains) == 2:
            return 6.0
        return 2.0

    def _score_asymmetry(self, url: str, text: str) -> float:
        # Check if it's from a mainstream source (lower asymmetry)
        for mainstream in self.MAINSTREAM_DOMAINS:
            if mainstream in url:
                return 2.0
        # Primary docs, arXiv, SEC, patent sources = high asymmetry
        high_asymmetry = ["arxiv.org", "sec.gov", "patents.google.com", "epo.org", "biorxiv.org"]
        for source in high_asymmetry:
            if source in url:
                return 9.5
        return 6.0

    def _generate_rationale(self, item: RawIntelItem, novelty, velocity, source_auth, actionability) -> str:
        parts = []
        if item.is_primary_source:
            parts.append("Primary source (regulatory/patent/academic)")
        if source_auth >= 8:
            parts.append(f"High-authority source: {item.source}")
        if actionability >= 6:
            parts.append("Contains actionable trigger words")
        if velocity >= 7:
            parts.append("High velocity trend")
        return ". ".join(parts) if parts else "Standard signal assessment."

    def batch_score(self, items: List[RawIntelItem], vector_store=None) -> List[Dict]:
        """Score all items and return sorted by score."""
        scored = []
        for item in items:
            velocity_count = 0
            if vector_store:
                try:
                    velocity_count = vector_store.count_similar_recent(item.title, hours=6)
                except Exception:
                    pass
            scored_item = self.score_item(item, velocity_count)
            scored.append(scored_item)

        scored.sort(key=lambda x: x["composite_score"], reverse=True)
        logger.info(f"[Scorer] Scored {len(scored)} items. Top score: {scored[0]['composite_score'] if scored else 0}")
        return scored
