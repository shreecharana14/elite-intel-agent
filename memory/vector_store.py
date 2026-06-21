"""
VectorStore: ChromaDB-powered semantic memory.
Enables deduplication and similarity search across all ingested intelligence.
"""
import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
from loguru import logger


class VectorStore:
    """
    Manages semantic memory using ChromaDB with Ollama embeddings.
    Used for:
    1. Deduplication (is this item semantically similar to something seen before?)
    2. Trend detection (how many similar items in the last N hours?)
    3. Context retrieval (find related past insights)
    """

    def __init__(self, data_dir: str = "./data/chromadb", collection_name: str = "intel_items"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        # Check if connecting to remote ChromaDB (Docker) or local
        chroma_host = os.getenv("CHROMA_HOST", "")
        if chroma_host:
            self.client = chromadb.HttpClient(
                host=chroma_host,
                port=int(os.getenv("CHROMA_PORT", "8001"))
            )
        else:
            self.client = chromadb.PersistentClient(
                path=data_dir,
                settings=Settings(anonymized_telemetry=False)
            )

        # Use Ollama for local embeddings
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

        try:
            self.embedding_fn = embedding_functions.OllamaEmbeddingFunction(
                url=f"{ollama_url}/api/embeddings",
                model_name=embed_model
            )
            logger.info(f"[VectorStore] Using Ollama embeddings: {embed_model}")
        except Exception:
            # Fallback to sentence-transformers if Ollama not available
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            logger.warning("[VectorStore] Ollama not available, using SentenceTransformers fallback")

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"[VectorStore] Collection '{collection_name}' ready. Items: {self.collection.count()}")

    def add_item(self, item_id: str, text: str, metadata: dict) -> bool:
        """Add an intelligence item to the vector store."""
        try:
            self.collection.add(
                documents=[text],
                ids=[item_id],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                return False  # Duplicate
            logger.error(f"[VectorStore] Failed to add item {item_id}: {e}")
            return False

    def is_duplicate(self, text: str, similarity_threshold: float = 0.92) -> bool:
        """Check if semantically similar content already exists."""
        if self.collection.count() == 0:
            return False

        results = self.collection.query(
            query_texts=[text],
            n_results=1
        )

        if results["distances"] and results["distances"][0]:
            similarity = 1 - results["distances"][0][0]  # cosine distance to similarity
            return similarity > similarity_threshold

        return False

    def get_related_items(self, text: str, n_results: int = 5, domain_filter: Optional[str] = None) -> List[Dict]:
        """Retrieve semantically related past intelligence items."""
        where = {"domain": domain_filter} if domain_filter else None
        try:
            results = self.collection.query(
                query_texts=[text],
                n_results=n_results,
                where=where
            )
            items = []
            for i, doc in enumerate(results["documents"][0]):
                items.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i],
                    "similarity": 1 - results["distances"][0][i]
                })
            return items
        except Exception as e:
            logger.error(f"[VectorStore] Query failed: {e}")
            return []

    def count_similar_recent(self, text: str, hours: int = 6) -> int:
        """Count how many similar items appeared in the last N hours (velocity signal)."""
        import time
        cutoff = time.time() - (hours * 3600)
        results = self.collection.query(
            query_texts=[text],
            n_results=20,
            where={"timestamp": {"$gte": cutoff}}
        )
        if not results["distances"] or not results["distances"][0]:
            return 0
        return sum(1 for d in results["distances"][0] if (1 - d) > 0.7)

    def get_stats(self) -> dict:
        """Return vector store statistics."""
        return {
            "total_items": self.collection.count(),
            "collection_name": self.collection.name
        }
