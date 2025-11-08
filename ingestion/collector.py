"""Document collection orchestrator with parallel fetching."""
import logging
import json
from typing import List, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import InterviewContext, Document
from config import DATA_DIR
from .sources import ALL_SOURCES

logger = logging.getLogger(__name__)


def _fetch_from_source(source_class, company: str, person: str) -> List[Dict[str, Any]]:
    """Helper to fetch from a single source (for parallel execution)."""
    try:
        source = source_class()
        return source.fetch(company, person)
    except Exception as e:
        logger.error(f"Error fetching from {source_class.__name__}: {e}")
        return []


def run_ingestion(company: str, person: str) -> Path:
    """
    Run parallel ingestion from all sources and save to JSONL.

    Args:
        company: Company name
        person: Person name

    Returns:
        Path to the output JSONL file
    """
    logger.info(f"Starting ingestion for {person} at {company}")

    all_results = []

    # Parallel fetch from all sources
    with ThreadPoolExecutor(max_workers=len(ALL_SOURCES)) as executor:
        # Submit all fetch tasks
        future_to_source = {
            executor.submit(_fetch_from_source, source_class, company, person): source_class
            for source_class in ALL_SOURCES
        }

        # Collect results as they complete
        for future in as_completed(future_to_source):
            source_class = future_to_source[future]
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Exception from {source_class.__name__}: {e}")

    logger.info(f"Total documents collected: {len(all_results)}")

    # Save to JSONL
    output_dir = DATA_DIR / company.replace(" ", "_").lower()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "source.jsonl"

    with open(output_file, "w") as f:
        for doc in all_results:
            f.write(json.dumps(doc) + "\n")

    logger.info(f"Saved to {output_file}")
    return output_file


def main(context: InterviewContext) -> List[Document]:
    """
    Collect relevant documents for interview preparation (backward compatible).

    Args:
        context: Interview context with company and person info

    Returns:
        List of Document objects with content and metadata
    """
    logger.info(f"Ingesting documents for {context.person} at {context.company}")

    # Run ingestion and save to file
    output_file = run_ingestion(context.company, context.person)

    # Load and convert to Document objects for backward compatibility
    documents = []
    with open(output_file, "r") as f:
        for line in f:
            doc_data = json.loads(line)
            documents.append(Document(
                content=doc_data["text"],
                source=doc_data["source"],
                metadata={"date": doc_data["date"]}
            ))

    logger.info(f"Collected {len(documents)} documents")
    return documents
