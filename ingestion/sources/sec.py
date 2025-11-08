"""SEC EDGAR API data source for 10-K and 10-Q filings."""
import requests
from typing import List, Dict, Any
from datetime import datetime
from .base import DataSource
from config import SEC_USER_AGENT, MAX_RESULTS_PER_SOURCE, REQUEST_TIMEOUT


class SECSource(DataSource):
    """Fetch SEC filings (10-K, 10-Q) via EDGAR API."""

    BASE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

    def fetch(self, company: str, person: str) -> List[Dict[str, Any]]:
        """
        Fetch SEC filings for the company.

        Uses SEC EDGAR full-text search to find 10-K and 10-Q filings.
        """
        results = []

        try:
            # SEC requires proper User-Agent header
            headers = {"User-Agent": SEC_USER_AGENT}

            # Search for company filings (10-K and 10-Q)
            for form_type in ["10-K", "10-Q"]:
                params = {
                    "action": "getcompany",
                    "company": company,
                    "type": form_type,
                    "dateb": "",  # No end date limit
                    "owner": "exclude",
                    "count": MAX_RESULTS_PER_SOURCE,
                    "output": "atom",  # XML format
                }

                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()

                # Parse basic info from response
                # In production, would parse XML properly
                if "no matching" not in response.text.lower():
                    results.append({
                        "source": f"SEC EDGAR - {form_type}",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "text": f"SEC {form_type} filing for {company}. "
                                f"[Full text would be extracted from EDGAR in production]"
                    })

        except requests.RequestException as e:
            self._log_fetch(0)
            # Don't fail entire ingestion if one source fails
            return []

        self._log_fetch(len(results))
        return results
