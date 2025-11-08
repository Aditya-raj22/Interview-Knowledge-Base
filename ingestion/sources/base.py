"""Base class for all data sources."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """Abstract base class for data sources."""

    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def fetch(self, company: str, person: str) -> List[Dict[str, Any]]:
        """
        Fetch documents from the data source.

        Args:
            company: Company name
            person: Person name

        Returns:
            List of dicts with keys: {source, date, text}
        """
        pass

    def _log_fetch(self, count: int):
        """Helper to log fetch results."""
        logger.info(f"{self.name}: Fetched {count} documents")
