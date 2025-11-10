"""
Science & IP Bot - Discovers scientific publications and intellectual property.

Searches for:
- PubMed research papers
- NIH RePORTER grants
- ClinicalTrials.gov trials
- Google Patents
"""

import requests
from typing import List
from .base import BaseBot, URLResult
from config import (
    PUBMED_API_KEY,
    SERPAPI_KEY,
    GOOGLE_SEARCH_API_KEY,
    GOOGLE_SEARCH_ENGINE_ID,
    REQUEST_TIMEOUT
)


class ScienceBot(BaseBot):
    """Discovers scientific publications, grants, trials, and patents."""

    @property
    def bot_name(self) -> str:
        return "science_bot"

    async def discover(self, person_name: str, company_name: str) -> List[URLResult]:
        """
        Discover science and IP URLs for the person and company.

        Returns up to 50 URLs from:
        - PubMed research papers
        - NIH RePORTER grants
        - ClinicalTrials.gov trials
        - Google Patents
        """
        results = []

        # 1. PubMed Research Papers
        results.extend(await self._search_pubmed(person_name, company_name))

        # 2. NIH RePORTER Grants
        results.extend(await self._search_nih_reporter(person_name, company_name))

        # 3. ClinicalTrials.gov
        results.extend(await self._search_clinical_trials(person_name, company_name))

        # 4. Patents
        results.extend(await self._search_patents(person_name, company_name))

        # Deduplicate and limit to max_results
        return self.deduplicate_results(results)

    async def _search_pubmed(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search PubMed for research papers."""
        results = []

        try:
            # Step 1: Search for PMIDs
            search_params = {
                "db": "pubmed",
                "term": f"{person_name}[Author] OR {company_name}[Affiliation]",
                "retmax": 30,
                "retmode": "json",
            }
            if PUBMED_API_KEY:
                search_params["api_key"] = PUBMED_API_KEY

            search_response = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params=search_params,
                timeout=REQUEST_TIMEOUT
            )
            search_response.raise_for_status()
            search_data = search_response.json()

            pmids = search_data.get("esearchresult", {}).get("idlist", [])

            # Step 2: Fetch article details for each PMID
            if pmids:
                fetch_params = {
                    "db": "pubmed",
                    "id": ",".join(pmids[:30]),
                    "retmode": "xml",
                }
                if PUBMED_API_KEY:
                    fetch_params["api_key"] = PUBMED_API_KEY

                fetch_response = requests.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                    params=fetch_params,
                    timeout=REQUEST_TIMEOUT
                )

                if fetch_response.ok:
                    # Parse XML to extract title, authors, date
                    # For simplicity, create direct PubMed links
                    for pmid in pmids[:30]:
                        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                        results.append(URLResult(
                            url=url,
                            title=f"PubMed Article {pmid}",
                            source="PubMed",
                            date="Unknown",
                            relevance_score=0.7,
                            description=f"Research article by {person_name} or affiliated with {company_name}"
                        ))

        except Exception as e:
            self.logger.warning(f"PubMed search failed: {e}")

        return results

    async def _search_nih_reporter(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search NIH RePORTER for research grants."""
        results = []

        try:
            # NIH RePORTER API v2
            url = "https://api.reporter.nih.gov/v2/projects/search"

            # Search by investigator name or organization
            payload = {
                "criteria": {
                    "pi_names": [{"any_name": person_name}],
                    "org_names": [company_name]
                },
                "offset": 0,
                "limit": 30,
                "sort_field": "project_start_date",
                "sort_order": "desc"
            }

            response = requests.post(
                url,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            if response.ok:
                data = response.json()
                for project in data.get("results", [])[:30]:
                    project_num = project.get("project_num", "")
                    title = project.get("project_title", "Untitled Grant")
                    fiscal_year = project.get("fiscal_year", "")
                    org_name = project.get("organization", {}).get("org_name", "")

                    # Create RePORTER URL
                    url = f"https://reporter.nih.gov/project-details/{project_num}"

                    relevance = self.calculate_relevance_score(
                        f"{title} {org_name}",
                        person_name,
                        company_name
                    )

                    results.append(URLResult(
                        url=url,
                        title=title,
                        source="NIH RePORTER",
                        date=f"{fiscal_year}-01-01" if fiscal_year else "Unknown",
                        relevance_score=relevance,
                        description=f"NIH grant {project_num}"
                    ))

        except Exception as e:
            self.logger.warning(f"NIH RePORTER search failed: {e}")

        return results

    async def _search_clinical_trials(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search ClinicalTrials.gov for clinical trials."""
        results = []

        try:
            # ClinicalTrials.gov API v2
            params = {
                "query.term": f"{company_name} OR {person_name}",
                "pageSize": 30,
                "format": "json",
            }

            response = requests.get(
                "https://clinicaltrials.gov/api/v2/studies",
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            if response.ok:
                data = response.json()
                for study in data.get("studies", []):
                    protocol = study.get("protocolSection", {})
                    id_module = protocol.get("identificationModule", {})

                    nct_id = id_module.get("nctId", "")
                    title = id_module.get("officialTitle") or id_module.get("briefTitle", "Untitled Study")

                    # Extract start date
                    status_module = protocol.get("statusModule", {})
                    start_date = status_module.get("startDateStruct", {}).get("date", "Unknown")

                    # Create ClinicalTrials.gov URL
                    url = f"https://clinicaltrials.gov/study/{nct_id}"

                    relevance = self.calculate_relevance_score(
                        title,
                        person_name,
                        company_name
                    )

                    results.append(URLResult(
                        url=url,
                        title=title,
                        source="ClinicalTrials.gov",
                        date=self.parse_date(start_date) or "Unknown",
                        relevance_score=relevance,
                        description=f"Clinical trial {nct_id}"
                    ))

        except Exception as e:
            self.logger.warning(f"ClinicalTrials.gov search failed: {e}")

        return results

    async def _search_patents(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search Google Patents."""
        results = []

        # Try SerpAPI first, then fall back to Google Custom Search
        if SERPAPI_KEY:
            results = await self._search_patents_serpapi(person_name, company_name)

        if not results and GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID:
            results = await self._search_patents_google(person_name, company_name)

        return results

    async def _search_patents_serpapi(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search patents using SerpAPI."""
        results = []

        try:
            params = {
                "engine": "google_patents",
                "q": f"{person_name} {company_name}",
                "api_key": SERPAPI_KEY,
                "num": 30,
            }

            response = requests.get(
                "https://serpapi.com/search",
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            if response.ok:
                data = response.json()
                for patent in data.get("organic_results", [])[:30]:
                    title = patent.get("title", "")
                    link = patent.get("pdf", "") or patent.get("link", "")
                    snippet = patent.get("snippet", "")
                    date = patent.get("priority_date", "Unknown")

                    relevance = self.calculate_relevance_score(
                        f"{title} {snippet}",
                        person_name,
                        company_name
                    )

                    results.append(URLResult(
                        url=link,
                        title=title,
                        source="Google Patents",
                        date=self.parse_date(date) or "Unknown",
                        relevance_score=relevance,
                        description=snippet
                    ))

        except Exception as e:
            self.logger.warning(f"SerpAPI patent search failed: {e}")

        return results

    async def _search_patents_google(self, person_name: str, company_name: str) -> List[URLResult]:
        """Fallback patent search using Google Custom Search."""
        results = []

        try:
            query = f"{person_name} {company_name} patent site:patents.google.com"

            params = {
                "key": GOOGLE_SEARCH_API_KEY,
                "cx": GOOGLE_SEARCH_ENGINE_ID,
                "q": query,
                "num": 30,
            }

            response = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            if response.ok:
                data = response.json()
                for item in data.get("items", [])[:30]:
                    url = item.get("link", "")
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    date = self.parse_date(snippet) or "Unknown"

                    relevance = self.calculate_relevance_score(
                        f"{title} {snippet}",
                        person_name,
                        company_name
                    )

                    results.append(URLResult(
                        url=url,
                        title=title,
                        source="Google Patents",
                        date=date,
                        relevance_score=relevance,
                        description=snippet
                    ))

        except Exception as e:
            self.logger.warning(f"Google patent search failed: {e}")

        return results
