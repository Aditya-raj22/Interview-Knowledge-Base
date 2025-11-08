"""Vectorization and NER for document chunks (backward compatible interface)."""
import logging
import hashlib
from typing import List
from models import Document, VectorChunk
from config import EMBEDDING_DIM, CHUNK_SIZE, MAX_CHUNKS_PER_DOC

logger = logging.getLogger(__name__)


def _mock_embed(text: str) -> List[float]:
    """Generate deterministic mock embedding using hash."""
    # Hash text to get deterministic vector, repeat hash cycles to reach EMBEDDING_DIM
    hash_bytes = hashlib.sha256(text.encode()).digest()
    # Repeat hash bytes to fill embedding dimension
    embedding = []
    while len(embedding) < EMBEDDING_DIM:
        embedding.extend([(b / 128.0) - 1.0 for b in hash_bytes])
    return embedding[:EMBEDDING_DIM]


def _extract_entities(text: str) -> List[str]:
    """Extract named entities (mock implementation using simple rules)."""
    # Mock NER - just find capitalized words as entities
    words = text.split()
    entities = [w.strip('.,!?') for w in words if w and w[0].isupper() and len(w) > 1]
    return list(set(entities))[:5]  # Limit to 5 unique entities


def _chunk_text(text: str) -> List[str]:
    """Split text into chunks."""
    chunks = []
    for i in range(0, len(text), CHUNK_SIZE):
        chunks.append(text[i:i + CHUNK_SIZE])
        if len(chunks) >= MAX_CHUNKS_PER_DOC:
            break
    return chunks


def main(documents: List[Document]) -> List[VectorChunk]:
    """
    Convert documents into vector chunks with embeddings and entities.

    NOTE: This is the legacy interface kept for backward compatibility.
    For production use with real embeddings, use build_index() instead.

    Args:
        documents: List of Document objects from ingestion

    Returns:
        List of VectorChunk objects with embeddings and NER entities
    """
    logger.info(f"Indexing {len(documents)} documents (legacy mock mode)")

    chunks = []
    for doc in documents:
        # Chunk the document
        text_chunks = _chunk_text(doc.content)

        for i, chunk_text in enumerate(text_chunks):
            # Generate embedding
            embedding = _mock_embed(chunk_text)

            # Extract entities
            entities = _extract_entities(chunk_text)

            # Create vector chunk
            chunk = VectorChunk(
                text=chunk_text,
                embedding=embedding,
                doc_id=f"{doc.source}#{i}",
                entities=entities
            )
            chunks.append(chunk)

    logger.info(f"Created {len(chunks)} vector chunks")
    return chunks
