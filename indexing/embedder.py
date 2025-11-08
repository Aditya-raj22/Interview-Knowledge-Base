"""Embedding generation with batching and caching."""
import logging
import hashlib
import json
import numpy as np
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
from config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    EMBEDDING_BATCH_SIZE,
    CACHE_EMBEDDINGS,
)

logger = logging.getLogger(__name__)


class Embedder:
    """Handles embedding generation with batching and caching."""

    def __init__(self, cache_dir: Path = None):
        """
        Initialize embedder with optional cache directory.

        Args:
            cache_dir: Directory to store embedding cache
        """
        self.client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.cache_dir = cache_dir
        self.cache = {}
        self._load_cache()

    def _load_cache(self):
        """Load embedding cache from disk if it exists."""
        if not CACHE_EMBEDDINGS or not self.cache_dir:
            return

        cache_file = self.cache_dir / "embedding_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached embeddings")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

    def _save_cache(self):
        """Save embedding cache to disk."""
        if not CACHE_EMBEDDINGS or not self.cache_dir:
            return

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / "embedding_cache.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(self.cache, f)
            logger.info(f"Saved {len(self.cache)} cached embeddings")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _hash_text(self, text: str) -> str:
        """Generate hash for text to use as cache key."""
        return hashlib.sha256(text.encode()).hexdigest()

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a batch of texts with caching.

        Args:
            texts: List of text strings to embed

        Returns:
            numpy array of shape (n_texts, embedding_dim)
        """
        if not self.client:
            logger.warning("No OpenAI API key, using mock embeddings")
            return self._mock_embeddings(texts)

        # Check cache for existing embeddings
        embeddings = []
        texts_to_embed = []
        text_indices = []

        for i, text in enumerate(texts):
            text_hash = self._hash_text(text)
            if CACHE_EMBEDDINGS and text_hash in self.cache:
                embeddings.append(self.cache[text_hash])
            else:
                texts_to_embed.append(text)
                text_indices.append(i)

        logger.info(
            f"Cache hit: {len(embeddings)}/{len(texts)}, "
            f"need to embed: {len(texts_to_embed)}"
        )

        # Embed texts not in cache in batches
        if texts_to_embed:
            new_embeddings = self._embed_api_batch(texts_to_embed)

            # Update cache
            if CACHE_EMBEDDINGS:
                for text, embedding in zip(texts_to_embed, new_embeddings):
                    text_hash = self._hash_text(text)
                    self.cache[text_hash] = embedding.tolist()
                self._save_cache()

            # Merge cached and new embeddings in correct order
            result = np.zeros((len(texts), EMBEDDING_DIM))
            cached_idx = 0
            new_idx = 0
            for i in range(len(texts)):
                if i in text_indices:
                    result[i] = new_embeddings[new_idx]
                    new_idx += 1
                else:
                    result[i] = embeddings[cached_idx]
                    cached_idx += 1
            return result
        else:
            return np.array(embeddings)

    def _embed_api_batch(self, texts: List[str]) -> np.ndarray:
        """Call OpenAI API to embed texts in batches."""
        all_embeddings = []

        # Process in batches to respect API limits
        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[i : i + EMBEDDING_BATCH_SIZE]
            logger.info(f"Embedding batch {i//EMBEDDING_BATCH_SIZE + 1}: {len(batch)} texts")

            try:
                response = self.client.embeddings.create(
                    input=batch, model=EMBEDDING_MODEL
                )
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Embedding API error: {e}")
                # Fall back to mock embeddings for this batch
                all_embeddings.extend(self._mock_embeddings(batch))

        return np.array(all_embeddings)

    def _mock_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate mock embeddings for testing without API key."""
        embeddings = []
        for text in texts:
            # Use hash to generate deterministic embedding
            hash_bytes = hashlib.sha256(text.encode()).digest()
            embedding = []
            while len(embedding) < EMBEDDING_DIM:
                embedding.extend([(b / 128.0) - 1.0 for b in hash_bytes])
            embeddings.append(embedding[:EMBEDDING_DIM])
        return np.array(embeddings)
