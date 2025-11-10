"""
News & Web Bot - Discovers news articles, press releases, and bios.

Searches for:
- Recent Google News articles
- Industry publications (Reuters, WSJ, BioPharma Dive, Endpoints)
- Company press releases
- Official biographies and profiles
"""

import requests
from typing import List
from datetime import datetime, timedelta
from .base import BaseBot, URLResult
from config import (
    GOOGLE_SEARCH_API_KEY,
    GOOGLE_SEARCH_ENGINE_ID,
    REQUEST_TIMEOUT
)


class NewsBot(BaseBot):
    """Discovers news articles, press releases, and biographical content."""

    @property
    def bot_name(self) -> str:
        return "news_bot"

    async def discover(self, person_name: str, company_name: str) -> List[URLResult]:
        """
        Discover news and web content URLs.

        Returns up to 50 URLs from:
        - Google News articles
        - Industry publications
        - Company press releases
        - Official biographies
        """
        results = []

        # 1. Google News Articles
        results.extend(await self._search_google_news(person_name, company_name))

        # 2. Industry Publications
        results.extend(await self._search_industry_news(person_name, company_name))

        # 3. Company Press Releases
        results.extend(await self._search_press_releases(person_name, company_name))

        # 4. Official Biographies and Profiles
        results.extend(await self._search_bios(person_name, company_name))

        # Deduplicate and limit to max_results
        return self.deduplicate_results(results)

    async def _search_google_news(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search Google News for recent articles."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            self.logger.warning("Google Search API not configured, skipping news search")
            return results

        # Search queries for news
        queries = [
            f"{person_name} {company_name} news",
            f"{person_name} announcement",
            f"{company_name} {person_name} latest",
        ]

        for query in queries:
            try:
                params = {
                    "key": GOOGLE_SEARCH_API_KEY,
                    "cx": GOOGLE_SEARCH_ENGINE_ID,
                    "q": query,
                    "num": 10,
                    "dateRestrict": "m6",  # Past 6 months
                    "sort": "date",  # Sort by date
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

                        # Extract date from snippet or metadata
                        date_str = item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time", "")
                        date = self.parse_date(date_str or snippet) or "Unknown"

                        relevance = self.calculate_relevance_score(
                            f"{title} {snippet}",
                            person_name,
                            company_name
                        )

                        results.append(URLResult(
                            url=url,
                            title=title,
                            source="Google News",
                            date=date,
                            relevance_score=relevance,
                            description=snippet
                        ))

            except Exception as e:
                self.logger.warning(f"Google News search failed for query '{query}': {e}")
                continue

        return results

    async def _search_industry_news(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search industry-specific publications."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        # Major industry publications
        publications = [
            "reuters.com",
            "wsj.com",
            "biopharmadive.com",
            "endpts.com",
            "fiercebiotech.com",
            "statnews.com",
            "bloomberg.com",
            "forbes.com",
        ]

        for site in publications[:4]:  # Limit to avoid too many API calls
            try:
                query = f"{person_name} {company_name} site:{site}"

                params = {
                    "key": GOOGLE_SEARCH_API_KEY,
                    "cx": GOOGLE_SEARCH_ENGINE_ID,
                    "q": query,
                    "num": 10,
                    "dateRestrict": "y2",  # Past 2 years
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

                        # Determine source from domain
                        source = site.replace(".com", "").title()

                        results.append(URLResult(
                            url=url,
                            title=title,
                            source=source,
                            date=date,
                            relevance_score=relevance,
                            description=snippet
                        ))

            except Exception as e:
                self.logger.warning(f"Industry news search failed for {site}: {e}")
                continue

        return results

    async def _search_press_releases(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search for company press releases."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        # Press release sites and company sites
        queries = [
            f"{company_name} press release {person_name}",
            f"{company_name} announces site:prnewswire.com",
            f"{company_name} news site:businesswire.com",
            f"{company_name} press release site:globenewswire.com",
        ]

        for query in queries:
            try:
                params = {
                    "key": GOOGLE_SEARCH_API_KEY,
                    "cx": GOOGLE_SEARCH_ENGINE_ID,
                    "q": query,
                    "num": 10,
                    "dateRestrict": "y2",  # Past 2 years
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

    async def _search_bios(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search for official biographies and profiles."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        # Biography-focused queries
        queries = [
            f"{person_name} {company_name} biography",
            f"{person_name} executive profile",
            f"{person_name} bio {company_name}",
            f"{person_name} leadership team site:{company_name.replace(' ', '').lower()}.com",
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
                            source="Biography",
                            date=date,
                            relevance_score=relevance,
                            description=snippet
                        ))

            except Exception as e:
                self.logger.warning(f"Biography search failed: {e}")
                continue

        return results
