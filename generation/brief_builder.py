"""Brief generation orchestrator - coordinates retrieval and generation."""
import logging
import time
from datetime import datetime
from typing import Dict, Any, List
from .retriever import SmartRetriever
from .prompter import BriefPrompter
from .generator import MultiModelGenerator
from config import GENERATION_MODEL, TOP_K_RESULTS, BRIEF_MODES

logger = logging.getLogger(__name__)


def generate_brief(
    company: str,
    person: str = None,
    mode: str = "summary",
    top_k: int = TOP_K_RESULTS,
    model: str = GENERATION_MODEL,
) -> Dict[str, Any]:
    """
    Generate an interview preparation brief using RAG.

    Args:
        company: Company name (index folder)
        person: Person name (optional, for context)
        mode: Brief mode (summary/technical/biographical/strategic)
        top_k: Number of chunks to retrieve
        model: LLM model to use

    Returns:
        Dict with keys:
            - summary: str (full generated text)
            - insights: List[Dict] with text and citations
            - key_entities: List[Dict] with type, text, mentions
            - citations: List[str] of chunk IDs
            - metadata: Dict with model, mode, timing, etc.
    """
    start_time = time.time()
    logger.info(f"Generating {mode} brief for {company}")

    # Validate mode
    if mode not in BRIEF_MODES:
        logger.warning(f"Invalid mode '{mode}', using 'summary'")
        mode = "summary"

    # Step 1: Initialize components
    retriever = SmartRetriever(company)
    prompter = BriefPrompter()
    generator = MultiModelGenerator(model)

    # Step 2: Retrieve relevant chunks
    retrieval_start = time.time()

    # Build query from person name if provided
    query = f"{person} at {company}" if person else f"{company} information"

    retrieved_chunks = retriever.retrieve(query, top_k=top_k, use_clusters=True)
    retrieval_time = time.time() - retrieval_start

    logger.info(f"Retrieved {len(retrieved_chunks)} chunks in {retrieval_time:.2f}s")

    # Step 3: Build prompts
    system_prompt, user_prompt = prompter.build_prompt(
        company=company,
        person=person or "the subject",
        mode=mode,
        retrieved_chunks=retrieved_chunks,
    )

    # Step 4: Generate response
    generation_start = time.time()
    generated_text = generator.generate(system_prompt, user_prompt)
    generation_time = time.time() - generation_start

    logger.info(f"Generated {len(generated_text)} chars in {generation_time:.2f}s")

    # Step 5: Extract structured information
    citations = generator.extract_citations(generated_text)

    # Extract insights (split by sections or paragraphs)
    insights = _extract_insights(generated_text, citations)

    # Aggregate entities from retrieved chunks
    key_entities = _aggregate_entities(retrieved_chunks)

    # Build result
    result = {
        "summary": generated_text,
        "insights": insights,
        "key_entities": key_entities,
        "citations": citations,
        "metadata": {
            "company": company,
            "person": person,
            "mode": mode,
            "model": model,
            "top_k": top_k,
            "n_chunks_retrieved": len(retrieved_chunks),
            "n_citations": len(citations),
            "retrieval_time_ms": int(retrieval_time * 1000),
            "generation_time_ms": int(generation_time * 1000),
            "total_time_ms": int((time.time() - start_time) * 1000),
            "timestamp": datetime.now().isoformat(),
        },
    }

    logger.info(
        f"Brief complete: {len(generated_text)} chars, "
        f"{len(insights)} insights, {len(citations)} citations"
    )

    return result


def _extract_insights(text: str, citations: List[str]) -> List[Dict[str, Any]]:
    """
    Extract structured insights from generated text.

    Args:
        text: Generated text
        citations: List of citation chunk IDs

    Returns:
        List of insight dicts with text and citations
    """
    insights = []

    # Split by markdown headers or bullet points
    sections = []

    # Find sections starting with ## or **
    import re
    lines = text.split("\n")
    current_section = []

    for line in lines:
        if line.startswith("##") or line.startswith("**") or line.startswith("- "):
            if current_section:
                sections.append("\n".join(current_section))
                current_section = []
            current_section.append(line)
        elif current_section:
            current_section.append(line)

    if current_section:
        sections.append("\n".join(current_section))

    # Extract citations from each section
    for section in sections:
        if len(section.strip()) > 20:  # Skip very short sections
            section_citations = re.findall(r'\[([^\]]+#\d+#\d+)\]', section)
            insights.append({
                "text": section.strip(),
                "citations": list(set(section_citations)),
            })

    # If no structured insights found, return full text as single insight
    if not insights:
        insights.append({"text": text, "citations": citations})

    return insights


def _aggregate_entities(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate and count entities from retrieved chunks.

    Args:
        chunks: List of retrieved chunk dicts

    Returns:
        List of entity dicts with type, text, and mention count
    """
    entity_counts = {}

    for chunk in chunks:
        for entity in chunk.get("entities", []):
            key = (entity["type"], entity["text"])
            if key not in entity_counts:
                entity_counts[key] = {
                    "type": entity["type"],
                    "text": entity["text"],
                    "mentions": 0,
                }
            entity_counts[key]["mentions"] += 1

    # Sort by mention count
    sorted_entities = sorted(
        entity_counts.values(), key=lambda x: x["mentions"], reverse=True
    )

    return sorted_entities[:10]  # Return top 10
