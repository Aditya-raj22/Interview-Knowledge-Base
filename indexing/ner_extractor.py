"""Named Entity Recognition with spaCy batching."""
import logging
from typing import List, Dict, Any
from config import SPACY_MODEL, SPACY_BATCH_SIZE

logger = logging.getLogger(__name__)


class NERExtractor:
    """Handles NER extraction with batched processing."""

    def __init__(self):
        """Initialize spaCy model (lazy import to avoid dependency issues)."""
        try:
            import spacy
            self.nlp = spacy.load(SPACY_MODEL)
            logger.info(f"Loaded spaCy model: {SPACY_MODEL}")
        except (OSError, ImportError) as e:
            logger.warning(f"spaCy model {SPACY_MODEL} not found or incompatible: {e}")
            logger.warning("Attempting to download...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", SPACY_MODEL])
            import spacy
            self.nlp = spacy.load(SPACY_MODEL)

    def extract_batch(self, texts: List[str]) -> List[List[Dict[str, str]]]:
        """
        Extract named entities from a batch of texts.

        Args:
            texts: List of text strings

        Returns:
            List of entity lists, where each entity is {type: str, text: str}
        """
        logger.info(f"Extracting entities from {len(texts)} texts")

        all_entities = []

        # Use spaCy's pipe for efficient batch processing
        # Disable unnecessary components for speed
        for doc in self.nlp.pipe(
            texts,
            batch_size=SPACY_BATCH_SIZE,
            disable=["lemmatizer", "textcat"],
        ):
            entities = [
                {"type": ent.label_, "text": ent.text}
                for ent in doc.ents
            ]
            all_entities.append(entities)

        total_entities = sum(len(e) for e in all_entities)
        logger.info(f"Extracted {total_entities} entities")

        return all_entities
