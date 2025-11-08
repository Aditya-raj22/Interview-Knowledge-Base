"""ClinicalTrials.gov API data source."""
import requests
from typing import List, Dict, Any
from datetime import datetime
from .base import DataSource
from config import MAX_RESULTS_PER_SOURCE, REQUEST_TIMEOUT


class ClinicalTrialsSource(DataSource):
    """Fetch clinical trial data from ClinicalTrials.gov API v2."""

    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    def fetch(self, company: str, person: str) -> List[Dict[str, Any]]:
        """
        Fetch clinical trials associated with company or person.

        Uses the new ClinicalTrials.gov API v2.
        """
        results = []

        try:
            # Search by company (sponsor) and person (principal investigator)
            params = {
                "query.term": f"{company} OR {person}",
                "pageSize": MAX_RESULTS_PER_SOURCE,
                "format": "json",
            }

            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            # Parse studies
            studies = data.get("studies", [])

            for study in studies:
                protocol = study.get("protocolSection", {})
                id_module = protocol.get("identificationModule", {})
                nct_id = id_module.get("nctId", "N/A")
                title = id_module.get("officialTitle", "Untitled Study")
                brief_summary = protocol.get("descriptionModule", {}).get("briefSummary", "")

                results.append({
                    "source": f"ClinicalTrials.gov {nct_id}",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "text": f"{title}. {brief_summary[:500]}"  # Limit summary length
                })

        except requests.RequestException as e:
            self._log_fetch(0)
            return []

        self._log_fetch(len(results))
        return results
