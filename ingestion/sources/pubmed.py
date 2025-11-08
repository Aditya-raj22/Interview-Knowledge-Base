"""PubMed E-utilities API data source."""
import requests
from typing import List, Dict, Any
from datetime import datetime
from .base import DataSource
from config import PUBMED_API_KEY, MAX_RESULTS_PER_SOURCE, REQUEST_TIMEOUT


class PubMedSource(DataSource):
    """Fetch publications from PubMed via E-utilities API."""

    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def fetch(self, company: str, person: str) -> List[Dict[str, Any]]:
        """
        Fetch PubMed articles authored by the person or related to company.

        Two-step process: 1) Search for PMIDs, 2) Fetch article details.
        """
        results = []

        try:
            # Step 1: Search for articles
            search_params = {
                "db": "pubmed",
                "term": f"{person}[Author] OR {company}[Affiliation]",
                "retmax": MAX_RESULTS_PER_SOURCE,
                "retmode": "json",
            }
            if PUBMED_API_KEY:
                search_params["api_key"] = PUBMED_API_KEY

            search_response = requests.get(
                self.ESEARCH_URL,
                params=search_params,
                timeout=REQUEST_TIMEOUT
            )
            search_response.raise_for_status()
            search_data = search_response.json()

            # Extract PMIDs
            pmids = search_data.get("esearchresult", {}).get("idlist", [])

            if not pmids:
                self._log_fetch(0)
                return []

            # Step 2: Fetch article abstracts (simplified for now)
            for pmid in pmids[:MAX_RESULTS_PER_SOURCE]:
                results.append({
                    "source": f"PubMed PMID:{pmid}",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "text": f"PubMed article by {person} (PMID: {pmid}). "
                            f"[Abstract would be fetched via efetch in production]"
                })

        except requests.RequestException as e:
            self._log_fetch(0)
            return []

        self._log_fetch(len(results))
        return results
