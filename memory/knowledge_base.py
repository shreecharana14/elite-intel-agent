"""
KnowledgeBase: SQLite-backed structured memory for intelligence items,
user preferences, scoring history, and feedback.
"""
import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from loguru import logger


class KnowledgeBase:
    """
    Persistent structured memory using SQLite.
    Stores: intelligence items, briefs, feedback, user preferences, scoring weights.
    """

    def __init__(self, data_dir: str = "./data"):
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = os.path.join(data_dir, "knowledge_base.db")
        self._init_db()
        logger.info(f"[KnowledgeBase] Initialized at {self.db_path}")

    def _init_db(self):
        """Create all tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS intel_items (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    source TEXT,
                    domain TEXT,
                    raw_summary TEXT,
                    timestamp TEXT,
                    composite_score REAL DEFAULT 0,
                    score_breakdown TEXT,
                    is_primary_source INTEGER DEFAULT 0,
                    included_in_brief INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS briefs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    item_ids TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    telegram_message_id TEXT,
                    whatsapp_sid TEXT
                );

                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    brief_id INTEGER,
                    item_id TEXT,
                    feedback_type TEXT,
                    rating INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (brief_id) REFERENCES briefs(id)
                );

                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS scoring_weights (
                    dimension TEXT PRIMARY KEY,
                    weight REAL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS seen_item_ids (
                    item_id TEXT PRIMARY KEY,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def get_seen_ids(self) -> set:
        """Load all previously seen item IDs for deduplication."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT item_id FROM seen_item_ids").fetchall()
            return {row[0] for row in rows}

    def mark_seen(self, item_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen_item_ids (item_id) VALUES (?)",
                (item_id,)
            )

    def store_item(self, item: dict):
        """Store a scored intelligence item."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO intel_items
                (id, title, url, source, domain, raw_summary, timestamp,
                 composite_score, score_breakdown, is_primary_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("id"),
                item.get("title"),
                item.get("url"),
                item.get("source"),
                json.dumps(item.get("domain", [])),
                item.get("raw_summary"),
                item.get("timestamp", datetime.now(timezone.utc).isoformat()),
                item.get("composite_score", 0),
                json.dumps(item.get("score_breakdown", {})),
                1 if item.get("is_primary_source") else 0
            ))

    def store_brief(self, content: str, item_ids: list, telegram_msg_id: str = None) -> int:
        """Store a delivered intelligence brief."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO briefs (content, item_ids, telegram_message_id)
                VALUES (?, ?, ?)
            """, (content, json.dumps(item_ids), telegram_msg_id))
            return cursor.lastrowid

    def store_feedback(self, brief_id: int, item_id: str, feedback_type: str, rating: int):
        """Store user feedback on an item."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO feedback (brief_id, item_id, feedback_type, rating)
                VALUES (?, ?, ?, ?)
            """, (brief_id, item_id, feedback_type, rating))

    def get_preference(self, key: str, default: Any = None) -> Any:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value FROM user_preferences WHERE key = ?", (key,)
            ).fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    return row[0]
            return default

    def set_preference(self, key: str, value: Any):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json.dumps(value)))

    def get_scoring_weights(self) -> Dict[str, float]:
        """Get current scoring weights (may have been adapted by LearningAgent)."""
        defaults = {
            "novelty": 0.25, "velocity": 0.20, "source_authority": 0.15,
            "actionability": 0.20, "cross_domain": 0.10, "asymmetry": 0.10
        }
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT dimension, weight FROM scoring_weights").fetchall()
            if not rows:
                return defaults
            return {row[0]: row[1] for row in rows}

    def update_scoring_weights(self, adjustments: Dict[str, float]):
        """Apply learning-based weight adjustments."""
        current = self.get_scoring_weights()
        with sqlite3.connect(self.db_path) as conn:
            for dimension, delta in adjustments.items():
                new_weight = max(0.05, min(0.50, current.get(dimension, 0.15) + delta))
                conn.execute("""
                    INSERT OR REPLACE INTO scoring_weights (dimension, weight, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (dimension, new_weight))

    def get_recent_feedback(self, limit: int = 50) -> List[Dict]:
        """Get recent user feedback for learning."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT f.feedback_type, f.rating, i.domain, i.source, i.composite_score
                FROM feedback f
                LEFT JOIN intel_items i ON f.item_id = i.id
                ORDER BY f.created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [
                {"feedback_type": r[0], "rating": r[1], "domain": r[2],
                 "source": r[3], "score": r[4]}
                for r in rows
            ]

    def get_stats(self) -> Dict:
        """Return system statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total_items = conn.execute("SELECT COUNT(*) FROM intel_items").fetchone()[0]
            total_briefs = conn.execute("SELECT COUNT(*) FROM briefs").fetchone()[0]
            total_feedback = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
            positive = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating > 0").fetchone()[0]
            return {
                "total_items_processed": total_items,
                "total_briefs_delivered": total_briefs,
                "total_feedback_received": total_feedback,
                "positive_feedback_rate": f"{(positive/max(total_feedback,1)*100):.0f}%"
            }
