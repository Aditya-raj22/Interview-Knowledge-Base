"""Base bot class for URL discovery with common utilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import hashlib
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging

logger = logging.getLogger(__name__)


@dataclass
class URLResult:
    """Standardized URL result with metadata."""

    url: str
    title: str
    source: str  # e.g., "SEC", "YouTube", "PubMed"
    date: Optional[str] = None  # ISO format YYYY-MM-DD or "Unknown"
    relevance_score: float = 0.0  # 0.0 to 1.0
    description: Optional[str] = None  # Brief description/snippet

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def __hash__(self):
        """Hash based on normalized URL for deduplication."""
        return hash(self.normalized_url())

    def normalized_url(self) -> str:
        """Return normalized URL for deduplication (remove tracking params)."""
        parsed = urlparse(self.url)
        query_params = parse_qs(parsed.query)

        # Remove common tracking parameters
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
            'fbclid', 'gclid', 'ref', 'source', '_ga', 'mc_cid', 'mc_eid'
        }
        clean_params = {k: v for k, v in query_params.items() if k not in tracking_params}

        # Rebuild URL without tracking params
        clean_query = urlencode(clean_params, doseq=True)
        clean_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            clean_query,
            ''  # Remove fragment
        ))

        return clean_url.rstrip('/')


class BaseBot(ABC):
    """
    Abstract base class for all URL finder bots.

    Each bot must implement discover() to return up to 50 relevant URLs
    for a given person and company combination.
    """

    def __init__(self, max_results: int = 50):
        """
        Initialize bot with result limit.

        Args:
            max_results: Maximum number of URLs to return (default 50)
        """
        self.max_results = max_results
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def discover(self, person_name: str, company_name: str) -> List[URLResult]:
        """
        Discover URLs relevant to the person and company.

        Args:
            person_name: Full name of the person to research
            company_name: Name of the company

        Returns:
            List of URLResult objects (up to max_results)
        """
        pass

    @property
    @abstractmethod
    def bot_name(self) -> str:
        """Return the bot's identifier (e.g., 'financial_bot')."""
        pass

    def calculate_relevance_score(self, text: str, person_name: str, company_name: str) -> float:
        """
        Calculate relevance score based on keyword presence.

        Args:
            text: Text to analyze (title + description)
            person_name: Person name to match
            company_name: Company name to match

        Returns:
            Relevance score between 0.0 and 1.0
        """
        text_lower = text.lower()
        score = 0.0

        # Person name match (40% weight)
        person_parts = person_name.lower().split()
        if all(part in text_lower for part in person_parts):
            score += 0.4
        elif any(part in text_lower for part in person_parts):
            score += 0.2

        # Company name match (40% weight)
        company_lower = company_name.lower()
        if company_lower in text_lower:
            score += 0.4
        elif any(word in text_lower for word in company_lower.split()):
            score += 0.2

        # Recency bonus (20% weight) - subclasses can override
        score += 0.2

        return min(score, 1.0)

    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parse various date formats to ISO format (YYYY-MM-DD).

        Args:
            date_str: Date string in various formats

        Returns:
            ISO formatted date string or None
        """
        if not date_str:
            return None

        # Common date patterns
        patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # 2024-01-15
            r'(\d{4})/(\d{2})/(\d{2})',  # 2024/01/15
            r'(\d{2})/(\d{2})/(\d{4})',  # 01/15/2024
            r'(\d{4})',                  # 2024 (year only)
        ]

        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    if len(groups[0]) == 4:  # YYYY-MM-DD or YYYY/MM/DD
                        return f"{groups[0]}-{groups[1]}-{groups[2]}"
                    else:  # MM/DD/YYYY
                        return f"{groups[2]}-{groups[0]}-{groups[1]}"
                elif len(groups) == 1:  # Year only
                    return f"{groups[0]}-01-01"

        return None

    def deduplicate_results(self, results: List[URLResult]) -> List[URLResult]:
        """
        Remove duplicate URLs based on normalized URLs.

        Args:
            results: List of URLResult objects

        Returns:
            Deduplicated list sorted by relevance score
        """
        seen_urls = set()
        unique_results = []

        for result in results:
            normalized = result.normalized_url()
            if normalized not in seen_urls:
                seen_urls.add(normalized)
                unique_results.append(result)

        # Sort by relevance score (highest first)
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return unique_results[:self.max_results]

    def filter_irrelevant(self, results: List[URLResult], min_score: float = 0.1) -> List[URLResult]:
        """
        Filter out results below minimum relevance threshold.

        Args:
            results: List of URLResult objects
            min_score: Minimum relevance score (default 0.1)

        Returns:
            Filtered list of results
        """
        return [r for r in results if r.relevance_score >= min_score]

    async def safe_discover(self, person_name: str, company_name: str) -> Dict[str, Any]:
        """
        Wrapper around discover() with error handling for API endpoint.

        Returns:
            Dictionary with bot name, results, and status
        """
        try:
            results = await self.discover(person_name, company_name)
            return {
                "name": self.bot_name,
                "status": "success",
                "count": len(results),
                "results": [r.to_dict() for r in results]
            }
        except Exception as e:
            self.logger.error(f"{self.bot_name} failed: {e}", exc_info=True)
            return {
                "name": self.bot_name,
                "status": "error",
                "count": 0,
                "results": [],
                "error": str(e)
            }
