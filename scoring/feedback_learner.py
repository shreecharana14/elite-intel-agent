"""
FeedbackLearner: Processes user reactions and updates scoring weights.
This is the self-learning engine that makes the system smarter over time.
"""
from typing import Dict, List
from loguru import logger
from memory.knowledge_base import KnowledgeBase


class FeedbackLearner:
    """
    Learns from user feedback (thumbs up/down) to continuously improve scoring.
    Uses a simple gradient-like approach to update dimension weights.
    """

    LEARNING_RATE = 0.05
    POSITIVE_BOOST = 0.15
    NEGATIVE_PENALTY = -0.20
    IGNORE_PENALTY = -0.05

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base

    def process_feedback(self, item_id: str, brief_id: int, reaction: str) -> Dict:
        """
        Process a single user reaction and update preferences.
        reaction: 'positive' (thumbs up), 'negative' (thumbs down), 'ignore'
        """
        rating = {
            "positive": 1,
            "negative": -1,
            "ignore": 0
        }.get(reaction, 0)

        self.kb.store_feedback(brief_id, item_id, reaction, rating)

        # Get domain of the rated item and adjust domain bias
        item_history = self._get_item_domain(item_id)
        if item_history:
            self._update_domain_bias(item_history, reaction)

        logger.info(f"[Learning] Processed feedback: {reaction} for item {item_id}")
        return {"status": "feedback_stored", "reaction": reaction, "item_id": item_id}

    def _get_item_domain(self, item_id: str) -> List[str]:
        import sqlite3, json
        with sqlite3.connect(self.kb.db_path) as conn:
            row = conn.execute(
                "SELECT domain FROM intel_items WHERE id = ?", (item_id,)
            ).fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    return []
        return []

    def _update_domain_bias(self, domains: List[str], reaction: str):
        """Update domain preference scores based on user reaction."""
        delta = {
            "positive": 0.05,
            "negative": -0.08,
            "ignore": -0.02
        }.get(reaction, 0)

        current_biases = self.kb.get_preference("domain_biases", {
            "ai": 1.0, "finance": 1.0, "geopolitics": 1.0,
            "biotech": 1.0, "quantum": 1.0, "energy": 1.0
        })

        for domain in domains:
            if domain in current_biases:
                new_bias = max(0.3, min(2.0, current_biases[domain] + delta))
                current_biases[domain] = round(new_bias, 3)

        self.kb.set_preference("domain_biases", current_biases)
        logger.debug(f"[Learning] Updated domain biases: {current_biases}")

    def run_learning_cycle(self) -> Dict:
        """
        Analyze all recent feedback and generate weight adjustments.
        Called periodically (e.g., every 24 hours).
        """
        feedback = self.kb.get_recent_feedback(limit=100)
        if len(feedback) < 5:
            return {"status": "insufficient_feedback", "samples": len(feedback)}

        # Analyze patterns
        positive = [f for f in feedback if f["rating"] > 0]
        negative = [f for f in feedback if f["rating"] < 0]

        # Identify top-performing domains
        domain_ratings = {}
        for f in feedback:
            domain = f.get("domain", "[]")
            if domain:
                import json
                try:
                    domains = json.loads(domain)
                except Exception:
                    domains = [domain]
                for d in domains:
                    if d not in domain_ratings:
                        domain_ratings[d] = []
                    domain_ratings[d].append(f["rating"])

        domain_avg = {d: sum(r)/len(r) for d, r in domain_ratings.items() if r}

        # Generate adjustments
        adjustments = {}
        if len(positive) > len(negative) * 2:
            # Users mostly upvoting -> boost source_authority and actionability
            adjustments["source_authority"] = self.LEARNING_RATE
            adjustments["actionability"] = self.LEARNING_RATE * 0.5
        elif len(negative) > len(positive):
            # Too much noise -> boost novelty and asymmetry filters
            adjustments["novelty"] = self.LEARNING_RATE
            adjustments["asymmetry"] = self.LEARNING_RATE
            adjustments["actionability"] = -self.LEARNING_RATE * 0.3

        self.kb.update_scoring_weights(adjustments)

        logger.info(f"[Learning] Cycle complete. Adjustments: {adjustments}")
        return {
            "status": "complete",
            "samples_analyzed": len(feedback),
            "positive": len(positive),
            "negative": len(negative),
            "weight_adjustments": adjustments,
            "domain_performance": domain_avg
        }
