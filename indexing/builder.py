"""Index builder orchestrator - coordinates embedding, NER, and clustering."""
import logging
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from .embedder import Embedder
from .ner_extractor import NERExtractor
from .clusterer import AdaptiveClusterer
from config import INDEX_DIR, EMBEDDING_MODEL, CHUNK_SIZE

logger = logging.getLogger(__name__)


def build_index(company_folder: str) -> Path:
    """
    Build index from raw JSONL data: embeddings + NER + clustering.

    Args:
        company_folder: Company name (folder name in data/raw/)

    Returns:
        Path to index directory

    Output structure:
        data/index/{company}/
        ├── embeddings.npy         # (N, 3072) array
        ├── entities.jsonl         # {chunk_id, entities: [{type, text}]}
        ├── clusters.json          # {cluster_id: [chunk_ids], metadata}
        └── metadata.json          # {model, timestamp, n_chunks}
    """
    logger.info(f"Building index for company: {company_folder}")

    # Setup paths
    from config import DATA_DIR
    raw_dir = DATA_DIR / company_folder
    index_dir = INDEX_DIR / company_folder
    index_dir.mkdir(parents=True, exist_ok=True)

    # Read raw JSONL data
    jsonl_file = raw_dir / "source.jsonl"
    if not jsonl_file.exists():
        raise FileNotFoundError(f"Raw data not found: {jsonl_file}")

    texts = []
    chunk_ids = []

    with open(jsonl_file, "r") as f:
        for i, line in enumerate(f):
            doc = json.loads(line)
            text = doc.get("text", "")

            # Chunk long texts
            for j, chunk_start in enumerate(range(0, len(text), CHUNK_SIZE)):
                chunk_text = text[chunk_start : chunk_start + CHUNK_SIZE]
                if chunk_text.strip():  # Skip empty chunks
                    texts.append(chunk_text)
                    chunk_ids.append(f"{doc['source']}#{i}#{j}")

    logger.info(f"Loaded {len(texts)} text chunks from {jsonl_file}")

    if not texts:
        logger.warning("No text chunks found, creating empty index")
        return index_dir

    # Step 1: Generate embeddings with caching
    embedder = Embedder(cache_dir=index_dir)
    embeddings = embedder.embed_batch(texts)
    logger.info(f"Generated embeddings: {embeddings.shape}")

    # Save embeddings
    embeddings_file = index_dir / "embeddings.npy"
    np.save(embeddings_file, embeddings)
    logger.info(f"Saved embeddings to {embeddings_file}")

    # Step 2: Extract entities with batching
    ner_extractor = NERExtractor()
    entities_list = ner_extractor.extract_batch(texts)

    # Save entities as JSONL
    entities_file = index_dir / "entities.jsonl"
    with open(entities_file, "w") as f:
        for chunk_id, entities in zip(chunk_ids, entities_list):
            f.write(json.dumps({"chunk_id": chunk_id, "entities": entities}) + "\n")
    logger.info(f"Saved entities to {entities_file}")

    # Step 3: Cluster embeddings
    clusterer = AdaptiveClusterer()
    cluster_result = clusterer.cluster(embeddings)

    # Build cluster map: cluster_id -> [chunk_ids]
    cluster_map = {}
    for chunk_id, label in zip(chunk_ids, cluster_result["labels"]):
        label_int = int(label)
        if label_int not in cluster_map:
            cluster_map[label_int] = []
        cluster_map[label_int].append(chunk_id)

    # Save clusters
    clusters_file = index_dir / "clusters.json"
    with open(clusters_file, "w") as f:
        json.dump(
            {
                "clusters": cluster_map,
                "n_clusters": cluster_result["n_clusters"],
                "silhouette_score": cluster_result["silhouette_score"],
                "cluster_sizes": cluster_result["cluster_sizes"],
            },
            f,
            indent=2,
        )
    logger.info(f"Saved clusters to {clusters_file}")

    # Save metadata
    metadata_file = index_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(
            {
                "company": company_folder,
                "embedding_model": EMBEDDING_MODEL,
                "n_chunks": len(texts),
                "timestamp": datetime.now().isoformat(),
            },
            f,
            indent=2,
        )
    logger.info(f"Saved metadata to {metadata_file}")

    logger.info(f"Index building complete: {index_dir}")
    return index_dir
