"""
Social Bot - Discovers professional social media content.

Searches for:
- Person's own Twitter/X posts (professional content)
- Person's LinkedIn activity and articles
- Professional mentions on Twitter/X
- Conference recordings and talks where they're mentioned
- Professional forum discussions (Hacker News, Reddit professional subs)
- Podcast/interview mentions
"""

import requests
from typing import List
from .base import BaseBot, URLResult
from config import (
    GOOGLE_SEARCH_API_KEY,
    GOOGLE_SEARCH_ENGINE_ID,
    REQUEST_TIMEOUT
)


class SocialBot(BaseBot):
    """Discovers professional social media content and mentions."""

    @property
    def bot_name(self) -> str:
        return "social_bot"

    async def discover(self, person_name: str, company_name: str) -> List[URLResult]:
        """
        Discover professional social media URLs.

        Returns up to 50 URLs from:
        - Person's Twitter/X posts
        - LinkedIn activity and articles
        - Professional mentions on social platforms
        - Conference/podcast mentions
        """
        results = []

        # 1. Person's own Twitter/X content
        results.extend(await self._search_twitter_own(person_name, company_name))

        # 2. Person's LinkedIn content (professional posts/articles)
        results.extend(await self._search_linkedin_content(person_name, company_name))

        # 3. Professional mentions on Twitter/X
        results.extend(await self._search_twitter_mentions(person_name, company_name))

        # 4. Conference and podcast mentions
        results.extend(await self._search_conference_mentions(person_name, company_name))

        # 5. Professional forum discussions
        results.extend(await self._search_professional_forums(person_name, company_name))

        # Deduplicate and limit to max_results
        return self.deduplicate_results(results)

    async def _search_twitter_own(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search for person's own Twitter/X posts."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            self.logger.warning("Google Search API not configured, skipping Twitter search")
            return results

        # Search for their Twitter profile and tweets
        queries = [
            f"{person_name} site:twitter.com OR site:x.com",
            f'"{person_name}" {company_name} site:twitter.com',
            f'"{person_name}" CEO site:twitter.com OR site:x.com',
        ]

        for query in queries:
            try:
                params = {
                    "key": GOOGLE_SEARCH_API_KEY,
                    "cx": GOOGLE_SEARCH_ENGINE_ID,
                    "q": query,
                    "num": 10,
                    "dateRestrict": "y2",  # Past 2 years for relevance
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

                        # Filter out non-professional content keywords
                        if self._is_professional_content(title, snippet):
                            date = self.parse_date(snippet) or "Unknown"
                            relevance = self.calculate_relevance_score(
                                f"{title} {snippet}",
                                person_name,
                                company_name
                            )

                            results.append(URLResult(
                                url=url,
                                title=title,
                                source="Twitter/X",
                                date=date,
                                relevance_score=relevance,
                                description=snippet
                            ))

            except Exception as e:
                self.logger.warning(f"Twitter search failed for query '{query}': {e}")
                continue

        return results

    async def _search_linkedin_content(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search for LinkedIn posts and articles by the person."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        queries = [
            f"{person_name} {company_name} site:linkedin.com/posts",
            f"{person_name} site:linkedin.com/pulse",
            f'"{person_name}" site:linkedin.com/in',  # Their profile
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
                            source="LinkedIn",
                            date=date,
                            relevance_score=relevance,
                            description=snippet
                        ))

            except Exception as e:
                self.logger.warning(f"LinkedIn search failed: {e}")
                continue

        return results

    async def _search_twitter_mentions(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search for professional mentions of the person on Twitter."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        # Focus on mentions from verified/professional accounts
        queries = [
            f'"{person_name}" {company_name} announcement site:twitter.com',
            f'"{person_name}" CEO interview site:twitter.com OR site:x.com',
            f'"{person_name}" speaking site:twitter.com',
        ]

        for query in queries:
            try:
                params = {
                    "key": GOOGLE_SEARCH_API_KEY,
                    "cx": GOOGLE_SEARCH_ENGINE_ID,
                    "q": query,
                    "num": 10,
                    "dateRestrict": "y1",  # Past year for recent mentions
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

                        if self._is_professional_content(title, snippet):
                            date = self.parse_date(snippet) or "Unknown"
                            relevance = self.calculate_relevance_score(
                                f"{title} {snippet}",
                                person_name,
                                company_name
                            )

                            results.append(URLResult(
                                url=url,
                                title=title,
                                source="Twitter Mention",
                                date=date,
                                relevance_score=relevance * 0.9,  # Slightly lower weight for mentions
                                description=snippet
                            ))

            except Exception as e:
                self.logger.warning(f"Twitter mentions search failed: {e}")
                continue

        return results

    async def _search_conference_mentions(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search for conference talks and podcast appearances."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        queries = [
            f'"{person_name}" conference speaker',
            f'"{person_name}" panel discussion',
            f'"{person_name}" {company_name} webinar',
            f'"{person_name}" keynote',
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
                            source="Conference/Event",
                            date=date,
                            relevance_score=relevance,
                            description=snippet
                        ))

            except Exception as e:
                self.logger.warning(f"Conference mentions search failed: {e}")
                continue

        return results

    async def _search_professional_forums(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search professional forums for discussions."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        # Focus on professional forums only
        queries = [
            f'"{person_name}" {company_name} site:news.ycombinator.com',
            f'"{person_name}" site:reddit.com/r/biotech',
            f'"{person_name}" site:reddit.com/r/science',
            f'"{person_name}" AMA site:reddit.com',
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

                        if self._is_professional_content(title, snippet):
                            date = self.parse_date(snippet) or "Unknown"
                            relevance = self.calculate_relevance_score(
                                f"{title} {snippet}",
                                person_name,
                                company_name
                            )

                            # Determine source from domain
                            if "ycombinator" in url:
                                source = "Hacker News"
                            elif "reddit" in url:
                                source = "Reddit"
                            else:
                                source = "Forum"

                            results.append(URLResult(
                                url=url,
                                title=title,
                                source=source,
                                date=date,
                                relevance_score=relevance * 0.85,  # Forum content slightly lower weight
                                description=snippet
                            ))

            except Exception as e:
                self.logger.warning(f"Forum search failed: {e}")
                continue

        return results

    def _is_professional_content(self, title: str, snippet: str) -> bool:
        """
        Filter out non-professional content.

        Returns True if content appears professional.
        """
        text_lower = f"{title} {snippet}".lower()

        # Professional keywords (positive indicators)
        professional_keywords = [
            "ceo", "founder", "interview", "speaking", "conference", "panel",
            "keynote", "announcement", "leadership", "strategy", "vision",
            "technology", "innovation", "research", "development", "company",
            "business", "industry", "market", "product", "launch"
        ]

        # Non-professional keywords (negative indicators - filter these out)
        unprofessional_keywords = [
            "gossip", "scandal", "drama", "personal life", "divorce",
            "dating", "relationship", "vacation", "party", "celebrity"
        ]

        # Check for unprofessional content first
        if any(keyword in text_lower for keyword in unprofessional_keywords):
            return False

        # Check for professional content
        if any(keyword in text_lower for keyword in professional_keywords):
            return True

        # Default to True (let relevance scoring handle it)
        return True
