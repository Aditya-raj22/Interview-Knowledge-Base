"""RAG-based generation for interview preparation."""
import logging
from typing import List
from models import VectorChunk
from config import TOP_K_RESULTS, MAX_RESPONSE_LENGTH

logger = logging.getLogger(__name__)


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = sum(a * a for a in vec1) ** 0.5
    mag2 = sum(b * b for b in vec2) ** 0.5
    return dot_product / (mag1 * mag2) if mag1 and mag2 else 0.0


def _retrieve_relevant_chunks(query: str, chunks: List[VectorChunk]) -> List[VectorChunk]:
    """Retrieve most relevant chunks for a query using mock embeddings."""
    # Import here to avoid circular dependency
    from indexing.vectorizer import _mock_embed

    query_embedding = _mock_embed(query)

    # Calculate similarities
    scored_chunks = [
        (chunk, _cosine_similarity(query_embedding, chunk.embedding))
        for chunk in chunks
    ]

    # Sort by similarity and take top K
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in scored_chunks[:TOP_K_RESULTS]]


def main(query: str, chunks: List[VectorChunk]) -> str:
    """
    Generate a response using RAG over the vector chunks.

    Args:
        query: User's question about the interview subject
        chunks: Indexed vector chunks from documents

    Returns:
        Generated response string
    """
    logger.info(f"Generating response for query: '{query}'")

    # Retrieve relevant chunks
    relevant_chunks = _retrieve_relevant_chunks(query, chunks)
    logger.info(f"Retrieved {len(relevant_chunks)} relevant chunks")

    # Mock generation - will be replaced with LLM call
    context_snippets = [chunk.text[:100] for chunk in relevant_chunks]
    entities = set()
    for chunk in relevant_chunks:
        entities.update(chunk.entities)

    response = (
        f"Based on the available information:\n\n"
        f"Key entities mentioned: {', '.join(list(entities)[:5])}\n\n"
        f"Relevant context: {' '.join(context_snippets[:2])}...\n\n"
        f"[Mock response - will be replaced with LLM-generated answer]"
    )

    # Truncate to max length
    response = response[:MAX_RESPONSE_LENGTH]
    logger.info(f"Generated response ({len(response)} chars)")

    return response
