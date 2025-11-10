"""
URL Discovery for NotebookLM Export
Finds all relevant URLs for a company/person without scraping content.
"""
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Set
from urllib.parse import urlparse, urljoin, parse_qs, urlunparse
from dataclasses import dataclass
import re
from config import GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_ENGINE_ID

logger = logging.getLogger(__name__)


@dataclass
class URLResult:
    """Represents a discovered URL with metadata."""
    url: str
    title: str
    snippet: str
    category: str
    relevance_score: float = 0.0


class URLDiscovery:
    """Discovers relevant URLs for NotebookLM import."""

    def __init__(self):
        self.discovered_urls: Set[str] = set()
        self.results: List[URLResult] = []

    def discover(self, company: str, person: str = None, max_urls: int = 50) -> List[URLResult]:
        """
        Discover all relevant URLs for a company/person.

        Args:
            company: Company name
            person: Person name (optional)
            max_urls: Maximum URLs to return (NotebookLM limit)

        Returns:
            List of URLResult objects, sorted by relevance
        """
        logger.info(f"Starting URL discovery for {company}" + (f" / {person}" if person else ""))

        # Step 1: Find company website
        company_domain = self._find_company_website(company)

        # Step 2: Discover URLs from multiple sources
        self._discover_google_search(company, person)
        self._discover_sec_filings(company)
        self._discover_youtube(company, person)
        self._discover_news(company, person)
        self._discover_podcasts(company, person)

        # Step 3: Parse company sitemap for subpages
        if company_domain:
            self._discover_sitemap(company_domain, company)

        # Step 4: Filter and rank
        self._deduplicate_urls()
        self._score_relevance(company, person)
        self._categorize_urls()

        # Step 5: Sort by relevance and limit
        sorted_results = sorted(self.results, key=lambda x: x.relevance_score, reverse=True)
        top_results = sorted_results[:max_urls]

        logger.info(f"Discovered {len(self.discovered_urls)} URLs, returning top {len(top_results)}")
        return top_results

    def _find_company_website(self, company: str) -> str:
        """Find the official company website domain."""
        try:
            query = f"{company} official website"
            url = f"https://www.googleapis.com/customsearch/v1"
            params = {
                "key": GOOGLE_SEARCH_API_KEY,
                "cx": GOOGLE_SEARCH_ENGINE_ID,
                "q": query,
                "num": 1
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("items"):
                website_url = data["items"][0]["link"]
                domain = urlparse(website_url).netloc
                logger.info(f"Found company website: {domain}")
                return domain

        except Exception as e:
            logger.warning(f"Could not find company website: {e}")

        return None

    def _discover_google_search(self, company: str, person: str = None):
        """Discover URLs using Google Custom Search API."""
        try:
            queries = [
                f"{company} about",
                f"{company} team leadership",
                f"{company} products services",
                f"{company} news press releases",
            ]

            if person:
                queries.append(f"{person} {company} interview")
                queries.append(f"{person} biography")

            url = f"https://www.googleapis.com/customsearch/v1"

            for query in queries:
                params = {
                    "key": GOOGLE_SEARCH_API_KEY,
                    "cx": GOOGLE_SEARCH_ENGINE_ID,
                    "q": query,
                    "num": 10
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                for item in data.get("items", []):
                    self.results.append(URLResult(
                        url=item["link"],
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                        category="web"
                    ))
                    self.discovered_urls.add(item["link"])

            logger.info(f"Google Search: Found {len(self.results)} URLs")

        except Exception as e:
            logger.warning(f"Google Search error: {e}")

    def _discover_sec_filings(self, company: str):
        """Discover SEC filing URLs directly."""
        try:
            # Search for company CIK
            search_url = f"https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                "action": "getcompany",
                "company": company,
                "type": "",
                "dateb": "",
                "owner": "exclude",
                "count": 10,
                "search_text": ""
            }

            headers = {"User-Agent": "Interview KB aditya.raj.fun@gmail.com"}
            response = requests.get(search_url, params=params, headers=headers, timeout=10)

            # Parse HTML to extract filing links (simplified)
            if "No matching" not in response.text:
                # Direct link to company filings
                filing_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={company.replace(' ', '+')}&type=&dateb=&owner=exclude&count=40"

                self.results.append(URLResult(
                    url=filing_url,
                    title=f"{company} SEC Filings",
                    snippet="SEC EDGAR company filings",
                    category="sec"
                ))
                self.discovered_urls.add(filing_url)

                logger.info(f"SEC: Found filing page")

        except Exception as e:
            logger.warning(f"SEC discovery error: {e}")

    def _discover_youtube(self, company: str, person: str = None):
        """Discover YouTube video URLs."""
        try:
            from config import YOUTUBE_API_KEY
            if not YOUTUBE_API_KEY:
                return

            queries = [f"{company} official"]
            if person:
                queries.append(f"{person} interview")
                queries.append(f"{person} {company}")

            url = "https://www.googleapis.com/youtube/v3/search"

            for query in queries:
                params = {
                    "key": YOUTUBE_API_KEY,
                    "q": query,
                    "part": "snippet",
                    "type": "video",
                    "maxResults": 10
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                for item in data.get("items", []):
                    video_id = item["id"]["videoId"]
                    video_url = f"https://www.youtube.com/watch?v={video_id}"

                    self.results.append(URLResult(
                        url=video_url,
                        title=item["snippet"]["title"],
                        snippet=item["snippet"]["description"][:200],
                        category="youtube"
                    ))
                    self.discovered_urls.add(video_url)

            logger.info(f"YouTube: Found {len([r for r in self.results if r.category == 'youtube'])} videos")

        except Exception as e:
            logger.warning(f"YouTube discovery error: {e}")

    def _discover_news(self, company: str, person: str = None):
        """Discover news article URLs."""
        try:
            # Use Google News search via Custom Search with news filter
            query = f"{company} news"
            if person:
                query = f"{person} {company} news"

            url = f"https://www.googleapis.com/customsearch/v1"
            params = {
                "key": GOOGLE_SEARCH_API_KEY,
                "cx": GOOGLE_SEARCH_ENGINE_ID,
                "q": query,
                "num": 10,
                "tbm": "nws"  # News search
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                self.results.append(URLResult(
                    url=item["link"],
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    category="news"
                ))
                self.discovered_urls.add(item["link"])

            logger.info(f"News: Found {len([r for r in self.results if r.category == 'news'])} articles")

        except Exception as e:
            logger.warning(f"News discovery error: {e}")

    def _discover_podcasts(self, company: str, person: str = None):
        """Discover podcast episode URLs (Spotify, Apple Podcasts via search)."""
        try:
            # Use general search for podcast platforms
            queries = []
            if person:
                queries.append(f"{person} podcast interview")
            queries.append(f"{company} podcast")

            url = f"https://www.googleapis.com/customsearch/v1"

            for query in queries:
                params = {
                    "key": GOOGLE_SEARCH_API_KEY,
                    "cx": GOOGLE_SEARCH_ENGINE_ID,
                    "q": query + " site:spotify.com OR site:podcasts.apple.com",
                    "num": 5
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                for item in data.get("items", []):
                    self.results.append(URLResult(
                        url=item["link"],
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                        category="podcast"
                    ))
                    self.discovered_urls.add(item["link"])

            logger.info(f"Podcasts: Found {len([r for r in self.results if r.category == 'podcast'])} episodes")

        except Exception as e:
            logger.warning(f"Podcast discovery error: {e}")

    def _discover_sitemap(self, domain: str, company: str):
        """Parse sitemap.xml to discover all company website subpages."""
        try:
            sitemap_urls = [
                f"https://{domain}/sitemap.xml",
                f"https://{domain}/sitemap_index.xml",
                f"https://www.{domain}/sitemap.xml",
            ]

            headers = {"User-Agent": "Interview KB Bot"}

            for sitemap_url in sitemap_urls:
                try:
                    response = requests.get(sitemap_url, headers=headers, timeout=10)
                    response.raise_for_status()

                    # Parse XML
                    root = ET.fromstring(response.content)

                    # Handle both sitemap and sitemap index
                    namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                    # Extract URLs
                    urls = root.findall(".//ns:loc", namespaces)

                    for url_elem in urls:
                        page_url = url_elem.text

                        # Filter relevant pages (skip unnecessary subpages)
                        if self._is_relevant_subpage(page_url, company):
                            self.results.append(URLResult(
                                url=page_url,
                                title=f"{company} - {self._extract_page_title(page_url)}",
                                snippet="Company website page",
                                category="company_site"
                            ))
                            self.discovered_urls.add(page_url)

                    logger.info(f"Sitemap: Found {len([r for r in self.results if r.category == 'company_site'])} pages")
                    break  # Found a working sitemap

                except requests.RequestException:
                    continue  # Try next sitemap URL

        except Exception as e:
            logger.warning(f"Sitemap parsing error: {e}")

    def _is_relevant_subpage(self, url: str, company: str) -> bool:
        """Filter out irrelevant subpages (pagination, search, etc.)."""
        # Relevant keywords in URL path
        relevant_keywords = [
            "about", "team", "leadership", "company", "mission",
            "product", "service", "technology", "innovation",
            "blog", "news", "press", "media", "contact"
        ]

        # Irrelevant patterns
        irrelevant_patterns = [
            r"\?page=\d+",  # Pagination
            r"/search",  # Search pages
            r"/category/",  # Category pages
            r"/tag/",  # Tag pages
            r"/author/",  # Author pages
            r"/\d{4}/\d{2}/\d{2}/",  # Date-based URLs (too many blog posts)
        ]

        url_lower = url.lower()

        # Check if URL contains relevant keywords
        has_relevant = any(keyword in url_lower for keyword in relevant_keywords)

        # Check if URL matches irrelevant patterns
        is_irrelevant = any(re.search(pattern, url) for pattern in irrelevant_patterns)

        return has_relevant and not is_irrelevant

    def _extract_page_title(self, url: str) -> str:
        """Extract a readable title from URL path."""
        path = urlparse(url).path
        segments = [s for s in path.split("/") if s]

        if segments:
            # Get last segment, clean it up
            title = segments[-1].replace("-", " ").replace("_", " ").title()
            return title

        return "Homepage"

    def _deduplicate_urls(self):
        """Remove duplicate URLs (normalize and dedupe)."""
        seen = set()
        unique_results = []

        for result in self.results:
            normalized = self._normalize_url(result.url)

            if normalized not in seen:
                seen.add(normalized)
                result.url = normalized  # Use normalized URL
                unique_results.append(result)

        self.results = unique_results
        logger.info(f"Deduplication: {len(self.results)} unique URLs")

    def _normalize_url(self, url: str) -> str:
        """Normalize URL (remove tracking params, fragments)."""
        parsed = urlparse(url)

        # Remove common tracking parameters
        query_params = parse_qs(parsed.query)
        tracking_params = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "ref", "source"]

        cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}

        # Rebuild query string
        from urllib.parse import urlencode
        cleaned_query = urlencode(cleaned_params, doseq=True)

        # Rebuild URL without fragment
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            cleaned_query,
            ""  # Remove fragment
        ))

        return normalized

    def _score_relevance(self, company: str, person: str = None):
        """Score each URL's relevance based on title/snippet."""
        company_terms = company.lower().split()
        person_terms = person.lower().split() if person else []

        for result in self.results:
            score = 0.0
            text = f"{result.title} {result.snippet}".lower()

            # Company name mentions
            for term in company_terms:
                score += text.count(term) * 2

            # Person name mentions
            for term in person_terms:
                score += text.count(term) * 3

            # Category bonuses
            category_bonus = {
                "company_site": 10,
                "sec": 8,
                "youtube": 6,
                "news": 5,
                "podcast": 5,
                "web": 3
            }
            score += category_bonus.get(result.category, 1)

            result.relevance_score = score

    def _categorize_urls(self):
        """Ensure all URLs are properly categorized."""
        for result in self.results:
            if result.category == "web":
                # Re-categorize based on URL domain
                domain = urlparse(result.url).netloc.lower()

                if "sec.gov" in domain:
                    result.category = "sec"
                elif "youtube.com" in domain or "youtu.be" in domain:
                    result.category = "youtube"
                elif "spotify.com" in domain or "podcasts.apple.com" in domain:
                    result.category = "podcast"
                elif any(news in domain for news in ["news", "bloomberg", "reuters", "wsj", "nytimes", "techcrunch"]):
                    result.category = "news"


def discover_urls(company: str, person: str = None, max_urls: int = 50) -> List[Dict[str, Any]]:
    """
    Main entry point for URL discovery.

    Args:
        company: Company name
        person: Person name (optional)
        max_urls: Maximum URLs to return

    Returns:
        List of dicts with url, title, snippet, category
    """
    discoverer = URLDiscovery()
    results = discoverer.discover(company, person, max_urls)

    # Convert to dict format
    return [
        {
            "url": r.url,
            "title": r.title,
            "snippet": r.snippet,
            "category": r.category,
            "score": r.relevance_score
        }
        for r in results
    ]
