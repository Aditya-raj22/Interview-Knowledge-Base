"""Google Patents data source via SerpAPI."""
import requests
from typing import List, Dict, Any
from datetime import datetime
from .base import DataSource
from config import SERPAPI_KEY, MAX_RESULTS_PER_SOURCE, REQUEST_TIMEOUT


class PatentsSource(DataSource):
    """Fetch patents from Google Patents via SerpAPI."""

    BASE_URL = "https://serpapi.com/search"

    def fetch(self, company: str, person: str) -> List[Dict[str, Any]]:
        """
        Fetch patents by company or inventor.

        Uses SerpAPI to search Google Patents.
        """
        results = []

        if not SERPAPI_KEY:
            # Skip if no API key provided
            self._log_fetch(0)
            return []

        try:
            # Search for patents by company or inventor
            params = {
                "engine": "google_patents",
                "q": f"{person} OR {company}",
                "num": MAX_RESULTS_PER_SOURCE,
                "api_key": SERPAPI_KEY,
            }

            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            # Parse patent results
            patents = data.get("organic_results", [])

            for patent in patents:
                title = patent.get("title", "Untitled Patent")
                patent_id = patent.get("patent_id", "N/A")
                snippet = patent.get("snippet", "")

                results.append({
                    "source": f"Google Patents {patent_id}",
                    "date": patent.get("filing_date", datetime.now().strftime("%Y-%m-%d")),
                    "text": f"{title}. {snippet}"
                })

        except requests.RequestException as e:
            self._log_fetch(0)
            return []

        self._log_fetch(len(results))
        return results
