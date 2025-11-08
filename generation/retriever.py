"""Smart retrieval with cluster-aware search."""
import logging
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from config import TOP_K_RESULTS, INDEX_DIR

logger = logging.getLogger(__name__)


class SmartRetriever:
    """Handles intelligent retrieval with cluster-aware optimization."""

    def __init__(self, company: str):
        """
        Initialize retriever for a company's index.

        Args:
            company: Company name (folder in INDEX_DIR)
        """
        self.company = company
        self.index_dir = INDEX_DIR / company
        self._load_index()

    def _load_index(self):
        """Load index files into memory."""
        logger.info(f"Loading index for {self.company}")

        # Load embeddings
        embeddings_file = self.index_dir / "embeddings.npy"
        if not embeddings_file.exists():
            raise FileNotFoundError(f"Index not found: {embeddings_file}")

        self.embeddings = np.load(embeddings_file)
        logger.info(f"Loaded {self.embeddings.shape[0]} embeddings")

        # Load entities
        self.entities = []
        entities_file = self.index_dir / "entities.jsonl"
        with open(entities_file, "r") as f:
            for line in f:
                self.entities.append(json.loads(line))

        # Load clusters
        clusters_file = self.index_dir / "clusters.json"
        with open(clusters_file, "r") as f:
            self.cluster_data = json.load(f)

        # Build chunk_id to index mapping
        self.chunk_id_to_idx = {
            ent["chunk_id"]: idx for idx, ent in enumerate(self.entities)
        }

        logger.info(f"Loaded {len(self.entities)} chunks across {self.cluster_data['n_clusters']} clusters")

    def _embed_query(self, query: str) -> np.ndarray:
        """
        Embed query using same model as index.

        Args:
            query: Query string

        Returns:
            Query embedding vector
        """
        from indexing.embedder import Embedder

        embedder = Embedder(cache_dir=self.index_dir)
        query_embedding = embedder.embed_batch([query])[0]
        return query_embedding

    def _find_relevant_clusters(self, query: str, top_clusters: int = 2) -> List[int]:
        """
        Find most relevant clusters based on entity matching.

        Args:
            query: Query string
            top_clusters: Number of clusters to return

        Returns:
            List of cluster IDs
        """
        query_lower = query.lower()
        cluster_scores = {}

        for cluster_id, chunk_ids in self.cluster_data["clusters"].items():
            score = 0
            # Score based on entity overlap
            for chunk_id in chunk_ids:
                if chunk_id in self.chunk_id_to_idx:
                    idx = self.chunk_id_to_idx[chunk_id]
                    entities = self.entities[idx]["entities"]
                    for entity in entities:
                        if entity["text"].lower() in query_lower:
                            score += 1

            cluster_scores[int(cluster_id)] = score

        # Return top clusters (or all if query matches none)
        sorted_clusters = sorted(cluster_scores.items(), key=lambda x: x[1], reverse=True)

        if sorted_clusters[0][1] > 0:
            # Return clusters with matches
            return [cid for cid, score in sorted_clusters[:top_clusters] if score > 0]
        else:
            # No entity matches - return all clusters
            return list(cluster_scores.keys())

    def retrieve(
        self, query: str, top_k: int = TOP_K_RESULTS, use_clusters: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant chunks for query.

        Args:
            query: Query string
            top_k: Number of chunks to return
            use_clusters: Whether to use cluster-aware search

        Returns:
            List of dicts with keys: chunk_id, text, entities, score, cluster_id
        """
        logger.info(f"Retrieving top-{top_k} chunks for query: '{query[:50]}...'")

        # Embed query
        query_embedding = self._embed_query(query)

        # Determine search space
        if use_clusters:
            relevant_clusters = self._find_relevant_clusters(query)
            logger.info(f"Searching in clusters: {relevant_clusters}")

            # Get chunk indices from relevant clusters
            candidate_chunk_ids = []
            for cluster_id in relevant_clusters:
                candidate_chunk_ids.extend(
                    self.cluster_data["clusters"][str(cluster_id)]
                )

            # Filter to valid indices
            candidate_indices = [
                self.chunk_id_to_idx[cid]
                for cid in candidate_chunk_ids
                if cid in self.chunk_id_to_idx
            ]
        else:
            # Search all chunks
            candidate_indices = list(range(len(self.embeddings)))

        logger.info(f"Searching {len(candidate_indices)} candidate chunks")

        # Calculate cosine similarities
        candidate_embeddings = self.embeddings[candidate_indices]
        similarities = np.dot(candidate_embeddings, query_embedding) / (
            np.linalg.norm(candidate_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get top-k
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Build results
        results = []
        for rank, idx in enumerate(top_indices):
            original_idx = candidate_indices[idx]
            entity_data = self.entities[original_idx]
            chunk_id = entity_data["chunk_id"]

            # Find cluster ID
            cluster_id = None
            for cid, cids in self.cluster_data["clusters"].items():
                if chunk_id in cids:
                    cluster_id = int(cid)
                    break

            # Load original text from JSONL
            text = self._load_chunk_text(chunk_id)

            results.append({
                "chunk_id": chunk_id,
                "text": text,
                "entities": entity_data["entities"],
                "score": float(similarities[idx]),
                "cluster_id": cluster_id,
                "rank": rank + 1,
            })

        logger.info(f"Retrieved {len(results)} chunks (avg score: {np.mean([r['score'] for r in results]):.3f})")
        return results

    def _load_chunk_text(self, chunk_id: str) -> str:
        """Load original text for a chunk ID from raw data."""
        # Parse chunk_id format: source#doc_idx#chunk_idx
        from config import DATA_DIR, CHUNK_SIZE

        parts = chunk_id.split("#")
        if len(parts) < 2:
            return "[Text not found]"

        source = "#".join(parts[:-2]) if len(parts) > 2 else parts[0]
        doc_idx = int(parts[-2]) if len(parts) > 2 else 0
        chunk_idx = int(parts[-1])

        # Load from raw JSONL
        jsonl_file = DATA_DIR / self.company / "source.jsonl"
        if not jsonl_file.exists():
            return "[Source file not found]"

        try:
            with open(jsonl_file, "r") as f:
                for i, line in enumerate(f):
                    if i == doc_idx:
                        doc = json.loads(line)
                        text = doc.get("text", "")
                        # Extract chunk
                        start = chunk_idx * CHUNK_SIZE
                        end = start + CHUNK_SIZE
                        return text[start:end]
        except Exception as e:
            logger.warning(f"Failed to load text for {chunk_id}: {e}")

        return "[Text loading error]"
