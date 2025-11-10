"""
Financial Bot - Discovers financial documents and SEC filings.

Searches for:
- SEC filings (S-1, 10-K, 10-Q, 8-K) from past 3 years
- Earnings call transcripts (SeekingAlpha, BAMSEC)
- Investor presentations and materials
- Financial press releases
"""

import requests
from typing import List
from datetime import datetime, timedelta
from .base import BaseBot, URLResult
from config import (
    SEC_USER_AGENT,
    GOOGLE_SEARCH_API_KEY,
    GOOGLE_SEARCH_ENGINE_ID,
    REQUEST_TIMEOUT
)


class FinancialBot(BaseBot):
    """Discovers financial documents, SEC filings, and investor materials."""

    @property
    def bot_name(self) -> str:
        return "financial_bot"

    async def discover(self, person_name: str, company_name: str) -> List[URLResult]:
        """
        Discover financial URLs for the person and company.

        Returns up to 50 URLs from:
        - SEC EDGAR filings (S-1, 10-K, 10-Q, 8-K)
        - Earnings call transcripts
        - Investor presentations
        - Financial press releases
        """
        results = []

        # 1. SEC EDGAR Filings (past 3 years)
        results.extend(await self._search_sec_filings(company_name))

        # 2. Earnings Call Transcripts
        results.extend(await self._search_transcripts(company_name, person_name))

        # 3. Investor Presentations
        results.extend(await self._search_investor_materials(company_name, person_name))

        # 4. Financial Press Releases
        results.extend(await self._search_press_releases(company_name, person_name))

        # Deduplicate and limit to max_results
        return self.deduplicate_results(results)

    async def _search_sec_filings(self, company_name: str) -> List[URLResult]:
        """Search SEC EDGAR for key filings from past 3 years."""
        results = []
        filing_types = ["S-1", "10-K", "10-Q", "8-K"]

        # Calculate date 3 years ago
        three_years_ago = (datetime.now() - timedelta(days=3*365)).strftime("%Y%m%d")

        headers = {"User-Agent": SEC_USER_AGENT}
        base_url = "https://www.sec.gov/cgi-bin/browse-edgar"

        for filing_type in filing_types:
            try:
                params = {
                    "action": "getcompany",
                    "company": company_name,
                    "type": filing_type,
                    "dateb": "",  # Current date
                    "datea": three_years_ago,  # 3 years ago
                    "owner": "exclude",
                    "count": 10,
                    "output": "atom"
                }

                response = requests.get(
                    base_url,
                    params=params,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                )

                if response.ok and "no matching" not in response.text.lower():
                    # Parse XML to extract filing URLs
                    # For now, create a search URL (users can browse from here)
                    search_url = response.url.replace("output=atom", "output=html")

                    results.append(URLResult(
                        url=search_url,
                        title=f"{company_name} - SEC {filing_type} Filings",
                        source="SEC EDGAR",
                        date=datetime.now().strftime("%Y-%m-%d"),
                        relevance_score=0.9,
                        description=f"SEC {filing_type} filings for {company_name} from the past 3 years"
                    ))

            except Exception as e:
                self.logger.warning(f"SEC filing search failed for {filing_type}: {e}")
                continue

        return results

    async def _search_transcripts(self, company_name: str, person_name: str) -> List[URLResult]:
        """Search for earnings call transcripts on SeekingAlpha and BAMSEC."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            self.logger.warning("Google Search API not configured, skipping transcript search")
            return results

        # Search queries for transcripts
        queries = [
            f"{company_name} earnings call transcript site:seekingalpha.com",
            f"{company_name} {person_name} earnings call transcript",
            f"{company_name} earnings transcript site:bamsec.com",
        ]

        for query in queries:
            try:
                params = {
                    "key": GOOGLE_SEARCH_API_KEY,
                    "cx": GOOGLE_SEARCH_ENGINE_ID,
                    "q": query,
                    "num": 10,
                }

                response = requests.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )

                if response.ok:
                    data = response.json()
                    for item in data.get("items", [])[:10]:
                        url = item.get("link", "")
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")

                        # Extract date from snippet if possible
                        date = self.parse_date(snippet) or "Unknown"

                        # Calculate relevance
                        relevance = self.calculate_relevance_score(
                            f"{title} {snippet}",
                            person_name,
                            company_name
                        )

                        results.append(URLResult(
                            url=url,
                            title=title,
                            source="Earnings Transcript",
                            date=date,
                            relevance_score=relevance,
                            description=snippet
                        ))

            except Exception as e:
                self.logger.warning(f"Transcript search failed for query '{query}': {e}")
                continue

        return results

    async def _search_investor_materials(self, company_name: str, person_name: str) -> List[URLResult]:
        """Search for investor presentations and materials."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        queries = [
            f"{company_name} investor presentation filetype:pdf",
            f"{company_name} investor relations {person_name}",
            f"{company_name} investor day presentation",
        ]

        for query in queries:
            try:
                params = {
                    "key": GOOGLE_SEARCH_API_KEY,
                    "cx": GOOGLE_SEARCH_ENGINE_ID,
                    "q": query,
                    "num": 10,
                }

                response = requests.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )

                if response.ok:
                    data = response.json()
                    for item in data.get("items", [])[:10]:
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
                            source="Investor Relations",
                            date=date,
                            relevance_score=relevance,
                            description=snippet
                        ))

            except Exception as e:
                self.logger.warning(f"Investor materials search failed: {e}")
                continue

        return results

    async def _search_press_releases(self, company_name: str, person_name: str) -> List[URLResult]:
        """Search for financial press releases."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        queries = [
            f"{company_name} financial results press release",
            f"{company_name} earnings press release",
            f"{company_name} {person_name} financial announcement",
        ]

        for query in queries:
            try:
                params = {
                    "key": GOOGLE_SEARCH_API_KEY,
                    "cx": GOOGLE_SEARCH_ENGINE_ID,
                    "q": query,
                    "num": 10,
                    "dateRestrict": "y3",  # Past 3 years
                }

                response = requests.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )

                if response.ok:
                    data = response.json()
                    for item in data.get("items", [])[:10]:
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
                            source="Press Release",
                            date=date,
                            relevance_score=relevance,
                            description=snippet
                        ))

            except Exception as e:
                self.logger.warning(f"Press release search failed: {e}")
                continue

        return results
