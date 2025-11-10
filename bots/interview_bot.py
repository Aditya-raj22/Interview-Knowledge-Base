"""
Interview Bot - Discovers interviews, talks, and authored content.

Searches for:
- Video interviews and conference talks (YouTube)
- Podcast interviews (Spotify, Apple Podcasts)
- Fireside chats and panel discussions
- LinkedIn posts authored by the person
- Blog posts and articles authored by the person
"""

import requests
from typing import List
from .base import BaseBot, URLResult
from config import (
    YOUTUBE_API_KEY,
    GOOGLE_SEARCH_API_KEY,
    GOOGLE_SEARCH_ENGINE_ID,
    REQUEST_TIMEOUT
)


class InterviewBot(BaseBot):
    """Discovers interviews, talks, podcasts, and authored content."""

    @property
    def bot_name(self) -> str:
        return "interview_bot"

    async def discover(self, person_name: str, company_name: str) -> List[URLResult]:
        """
        Discover interview and authored content URLs.

        Returns up to 50 URLs from:
        - YouTube interviews and talks
        - Podcast episodes
        - LinkedIn posts
        - Blog posts and articles
        """
        results = []

        # 1. YouTube Videos (interviews, talks, presentations)
        results.extend(await self._search_youtube(person_name, company_name))

        # 2. Podcast Interviews
        results.extend(await self._search_podcasts(person_name, company_name))

        # 3. LinkedIn Posts
        results.extend(await self._search_linkedin(person_name, company_name))

        # 4. Blog Posts and Articles
        results.extend(await self._search_blogs(person_name, company_name))

        # Deduplicate and limit to max_results
        return self.deduplicate_results(results)

    async def _search_youtube(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search YouTube for interviews, talks, and presentations."""
        results = []

        if not YOUTUBE_API_KEY:
            self.logger.warning("YouTube API not configured, using Google Search fallback")
            return await self._search_youtube_fallback(person_name, company_name)

        # Search queries for different types of content
        queries = [
            f"{person_name} {company_name} interview",
            f"{person_name} keynote speech",
            f"{person_name} fireside chat",
            f"{person_name} conference talk",
        ]

        for query in queries:
            try:
                params = {
                    "key": YOUTUBE_API_KEY,
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "maxResults": 10,
                    "order": "relevance",
                }

                response = requests.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )

                if response.ok:
                    data = response.json()
                    for item in data.get("items", []):
                        video_id = item["id"].get("videoId")
                        if not video_id:
                            continue

                        snippet = item.get("snippet", {})
                        title = snippet.get("title", "")
                        description = snippet.get("description", "")
                        published_at = snippet.get("publishedAt", "")

                        # Parse date
                        date = self.parse_date(published_at) or "Unknown"

                        # Calculate relevance
                        relevance = self.calculate_relevance_score(
                            f"{title} {description}",
                            person_name,
                            company_name
                        )

                        results.append(URLResult(
                            url=f"https://www.youtube.com/watch?v={video_id}",
                            title=title,
                            source="YouTube",
                            date=date,
                            relevance_score=relevance,
                            description=description[:200]
                        ))

            except Exception as e:
                self.logger.warning(f"YouTube search failed for query '{query}': {e}")
                continue

        return results

    async def _search_youtube_fallback(self, person_name: str, company_name: str) -> List[URLResult]:
        """Fallback to Google Search for YouTube videos."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        queries = [
            f"{person_name} {company_name} interview site:youtube.com",
            f"{person_name} keynote site:youtube.com",
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
                            source="YouTube",
                            date=date,
                            relevance_score=relevance,
                            description=snippet
                        ))

            except Exception as e:
                self.logger.warning(f"YouTube fallback search failed: {e}")
                continue

        return results

    async def _search_podcasts(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search for podcast interviews on Spotify, Apple Podcasts, etc."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        queries = [
            f"{person_name} podcast interview",
            f"{person_name} {company_name} podcast site:spotify.com",
            f"{person_name} podcast site:podcasts.apple.com",
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
                            source="Podcast",
                            date=date,
                            relevance_score=relevance,
                            description=snippet
                        ))

            except Exception as e:
                self.logger.warning(f"Podcast search failed: {e}")
                continue

        return results

    async def _search_linkedin(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search for LinkedIn posts authored by the person."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        # LinkedIn search queries
        queries = [
            f"{person_name} site:linkedin.com/posts",
            f"{person_name} {company_name} site:linkedin.com/pulse",
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

    async def _search_blogs(self, person_name: str, company_name: str) -> List[URLResult]:
        """Search for blog posts and articles authored by the person."""
        results = []

        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return results

        queries = [
            f"{person_name} blog post author",
            f'"{person_name}" blog {company_name}',
            f"{person_name} medium article",
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
                            source="Blog",
                            date=date,
                            relevance_score=relevance,
                            description=snippet
                        ))

            except Exception as e:
                self.logger.warning(f"Blog search failed: {e}")
                continue

        return results
