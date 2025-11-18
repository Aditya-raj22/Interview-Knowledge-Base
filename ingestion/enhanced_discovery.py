"""
Enhanced URL Discovery with Additional APIs
Adds high-impact sources for 3-5x more URLs
"""
import logging
import requests
from typing import List, Dict, Any
from dataclasses import dataclass
from config import (
    GOOGLE_SEARCH_API_KEY,
    GOOGLE_SEARCH_ENGINE_ID,
    YOUTUBE_API_KEY,
)

logger = logging.getLogger(__name__)


@dataclass
class URLResult:
    url: str
    title: str
    snippet: str
    category: str
    relevance_score: float = 0.0


class EnhancedURLDiscovery:
    """
    Enhanced discovery with additional high-impact APIs.

    NEW SOURCES ADDED:
    - Reddit (discussions, AMAs)
    - Hacker News (tech discussions)
    - Medium (direct API)
    - NewsAPI (comprehensive news)
    - Semantic Scholar (academic papers)
    - Listen Notes (podcasts)
    """

    def __init__(self):
        self.results: List[URLResult] = []
        self.discovered_urls = set()

    # =========================================================================
    # REDDIT DISCOVERY (Discussions, AMAs)
    # =========================================================================

    def _discover_reddit(self, company: str, person: str = None):
        """
        Discover Reddit discussions, AMAs, mentions.
        Uses Reddit API (no key needed for public data).
        """
        logger.info("🔍 Discovering Reddit content...")

        try:
            search_terms = [company]
            if person:
                search_terms.append(person)

            for term in search_terms:
                # Search subreddits
                url = "https://www.reddit.com/search.json"
                params = {
                    "q": term,
                    "sort": "relevance",
                    "limit": 25
                }
                headers = {"User-Agent": "InterviewKB/1.0"}

                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                for post in data.get("data", {}).get("children", []):
                    post_data = post["data"]
                    permalink = f"https://www.reddit.com{post_data['permalink']}"

                    if permalink not in self.discovered_urls:
                        self.results.append(URLResult(
                            url=permalink,
                            title=post_data["title"],
                            snippet=post_data.get("selftext", "")[:200],
                            category="social"  # or "thought_leadership" if AMA
                        ))
                        self.discovered_urls.add(permalink)

            logger.info(f"Reddit: Found {len([r for r in self.results if 'reddit.com' in r.url])} discussions")

        except Exception as e:
            logger.warning(f"Reddit discovery error: {e}")

    # =========================================================================
    # HACKER NEWS DISCOVERY
    # =========================================================================

    def _discover_hackernews(self, company: str, person: str = None):
        """
        Discover Hacker News discussions, Show HN posts.
        Uses Algolia HN Search API (free, no key).
        """
        logger.info("🔍 Discovering Hacker News content...")

        try:
            search_terms = [company]
            if person:
                search_terms.append(person)

            for term in search_terms:
                url = "https://hn.algolia.com/api/v1/search"
                params = {
                    "query": term,
                    "tags": "story",
                    "hitsPerPage": 50
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                for hit in data.get("hits", []):
                    if hit.get("url"):
                        # Add HN discussion page
                        hn_url = f"https://news.ycombinator.com/item?id={hit['objectID']}"

                        if hn_url not in self.discovered_urls:
                            self.results.append(URLResult(
                                url=hn_url,
                                title=hit["title"],
                                snippet=f"HN discussion - {hit.get('points', 0)} points, {hit.get('num_comments', 0)} comments",
                                category="thought_leadership"
                            ))
                            self.discovered_urls.add(hn_url)

                        # Add original article if exists
                        original_url = hit.get("url")
                        if original_url and original_url not in self.discovered_urls:
                            self.results.append(URLResult(
                                url=original_url,
                                title=hit["title"],
                                snippet=f"Discussed on HN",
                                category="thought_leadership"
                            ))
                            self.discovered_urls.add(original_url)

            logger.info(f"HN: Found {len([r for r in self.results if 'ycombinator.com' in r.url])} discussions")

        except Exception as e:
            logger.warning(f"Hacker News discovery error: {e}")

    # =========================================================================
    # MEDIUM DIRECT API
    # =========================================================================

    def _discover_medium(self, company: str, person: str = None):
        """
        Discover Medium articles directly (better than Google Search).
        Uses Medium's RSS feeds (no API key needed).
        """
        logger.info("🔍 Discovering Medium articles...")

        try:
            # Medium RSS search via Google
            search_term = person or company

            # Search Medium via site: operator (more reliable than Medium API)
            if GOOGLE_SEARCH_API_KEY:
                self._google_search(
                    f"{search_term} site:medium.com",
                    "thought_leadership",
                    num_results=20
                )

        except Exception as e:
            logger.warning(f"Medium discovery error: {e}")

    # =========================================================================
    # NEWS API (Comprehensive News Coverage)
    # =========================================================================

    def _discover_news_api(self, company: str, person: str = None, api_key: str = None):
        """
        Discover news articles via NewsAPI.
        Covers 80,000+ sources worldwide.

        Get free key at: https://newsapi.org/
        """
        if not api_key:
            logger.warning("NewsAPI key not configured, skipping")
            return

        logger.info("🔍 Discovering news via NewsAPI...")

        try:
            search_term = f"{person} {company}" if person else company

            url = "https://newsapi.org/v2/everything"
            params = {
                "apiKey": api_key,
                "q": search_term,
                "sortBy": "relevancy",
                "pageSize": 100,
                "language": "en"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for article in data.get("articles", []):
                article_url = article.get("url")

                if article_url and article_url not in self.discovered_urls:
                    self.results.append(URLResult(
                        url=article_url,
                        title=article["title"],
                        snippet=article.get("description", ""),
                        category="news"
                    ))
                    self.discovered_urls.add(article_url)

            logger.info(f"NewsAPI: Found {len([r for r in self.results if r.category == 'news'])} articles")

        except Exception as e:
            logger.warning(f"NewsAPI error: {e}")

    # =========================================================================
    # SEMANTIC SCHOLAR (Academic Papers)
    # =========================================================================

    def _discover_semantic_scholar(self, company: str, person: str = None):
        """
        Discover academic papers via Semantic Scholar API.
        200M+ papers, free API, no key needed.
        """
        logger.info("🔍 Discovering academic papers...")

        try:
            search_term = person or company

            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                "query": search_term,
                "limit": 50,
                "fields": "title,abstract,url,authors,year,citationCount"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for paper in data.get("data", []):
                paper_url = paper.get("url")

                if paper_url and paper_url not in self.discovered_urls:
                    authors = ", ".join([a.get("name", "") for a in paper.get("authors", [])[:3]])

                    self.results.append(URLResult(
                        url=paper_url,
                        title=paper["title"],
                        snippet=f"{authors} ({paper.get('year', 'N/A')}) - {paper.get('citationCount', 0)} citations",
                        category="technical"
                    ))
                    self.discovered_urls.add(paper_url)

            logger.info(f"Semantic Scholar: Found {len([r for r in self.results if 'semanticscholar.org' in r.url])} papers")

        except Exception as e:
            logger.warning(f"Semantic Scholar error: {e}")

    # =========================================================================
    # LISTEN NOTES (Podcast Aggregator)
    # =========================================================================

    def _discover_listen_notes(self, company: str, person: str = None, api_key: str = None):
        """
        Discover podcast episodes via Listen Notes API.
        800,000+ podcasts indexed.

        Get free key at: https://www.listennotes.com/api/
        Free tier: 30 requests/month
        """
        if not api_key or not person:
            logger.warning("Listen Notes API key not configured or no person specified")
            return

        logger.info("🔍 Discovering podcasts via Listen Notes...")

        try:
            url = "https://listen-api.listennotes.com/api/v2/search"
            headers = {"X-ListenAPI-Key": api_key}
            params = {
                "q": f"{person} {company}",
                "type": "episode",
                "sort_by_date": 0,  # Sort by relevance
                "len_min": 10,      # At least 10 minutes
                "only_in": "title,description",
                "language": "English"
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            for episode in data.get("results", []):
                episode_url = episode.get("link")

                if episode_url and episode_url not in self.discovered_urls:
                    self.results.append(URLResult(
                        url=episode_url,
                        title=episode["title_original"],
                        snippet=f"{episode.get('podcast_title_original', '')} - {episode.get('description_original', '')[:200]}",
                        category="podcast"
                    ))
                    self.discovered_urls.add(episode_url)

            logger.info(f"Listen Notes: Found {len([r for r in self.results if r.category == 'podcast'])} episodes")

        except Exception as e:
            logger.warning(f"Listen Notes error: {e}")

    # =========================================================================
    # TWITTER/X DISCOVERY
    # =========================================================================

    def _discover_twitter(self, company: str, person: str = None, bearer_token: str = None):
        """
        Discover Twitter/X profiles and tweets.
        Uses Twitter API v2.

        Get bearer token at: https://developer.twitter.com/
        """
        if not bearer_token:
            logger.warning("Twitter API bearer token not configured")
            return

        logger.info("🔍 Discovering Twitter content...")

        try:
            headers = {"Authorization": f"Bearer {bearer_token}"}

            # Search for user
            search_term = person or company
            url = "https://api.twitter.com/2/users/by"
            params = {"usernames": search_term.replace(" ", "").lower()}

            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                for user in data.get("data", []):
                    username = user["username"]
                    profile_url = f"https://twitter.com/{username}"

                    if profile_url not in self.discovered_urls:
                        self.results.append(URLResult(
                            url=profile_url,
                            title=f"@{username} on Twitter/X",
                            snippet=f"Twitter profile",
                            category="social"
                        ))
                        self.discovered_urls.add(profile_url)

            logger.info(f"Twitter: Found {len([r for r in self.results if 'twitter.com' in r.url])} profiles")

        except Exception as e:
            logger.warning(f"Twitter discovery error: {e}")

    # =========================================================================
    # HELPER: Google Search (reuse from main discovery)
    # =========================================================================

    def _google_search(self, query: str, category: str, num_results: int = 10):
        """Perform Google Custom Search."""
        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return

        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": GOOGLE_SEARCH_API_KEY,
                "cx": GOOGLE_SEARCH_ENGINE_ID,
                "q": query,
                "num": min(num_results, 10)
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                url_str = item["link"]

                if url_str not in self.discovered_urls:
                    self.results.append(URLResult(
                        url=url_str,
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                        category=category
                    ))
                    self.discovered_urls.add(url_str)

        except Exception as e:
            logger.warning(f"Google search error: {e}")


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

def discover_urls_enhanced(
    company: str,
    person: str = None,
    newsapi_key: str = None,
    listennotes_key: str = None,
    twitter_token: str = None
) -> List[Dict[str, Any]]:
    """
    Enhanced URL discovery with additional sources.

    Args:
        company: Company name
        person: Person name (optional)
        newsapi_key: NewsAPI key (optional but recommended)
        listennotes_key: Listen Notes API key (optional)
        twitter_token: Twitter API bearer token (optional)

    Returns:
        List of discovered URLs with metadata
    """
    discoverer = EnhancedURLDiscovery()

    # Run all discovery methods
    discoverer._discover_reddit(company, person)
    discoverer._discover_hackernews(company, person)
    discoverer._discover_medium(company, person)
    discoverer._discover_semantic_scholar(company, person)

    # Optional APIs (if keys provided)
    if newsapi_key:
        discoverer._discover_news_api(company, person, newsapi_key)
    if listennotes_key and person:
        discoverer._discover_listen_notes(company, person, listennotes_key)
    if twitter_token:
        discoverer._discover_twitter(company, person, twitter_token)

    return [
        {
            "url": r.url,
            "title": r.title,
            "snippet": r.snippet,
            "category": r.category,
            "score": r.relevance_score
        }
        for r in discoverer.results
    ]
