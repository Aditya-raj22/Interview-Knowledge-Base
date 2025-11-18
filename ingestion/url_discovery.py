"""
Comprehensive URL Discovery for NotebookLM Export
Discovers ALL relevant URLs for a company/person across multiple categories.
"""
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Set
from urllib.parse import urlparse, urljoin, parse_qs, urlunparse, urlencode
from dataclasses import dataclass
import re
from config import (
    GOOGLE_SEARCH_API_KEY,
    GOOGLE_SEARCH_ENGINE_ID,
    YOUTUBE_API_KEY,
    SERPAPI_KEY
)

logger = logging.getLogger(__name__)


@dataclass
class URLResult:
    """Represents a discovered URL with metadata."""
    url: str
    title: str
    snippet: str
    category: str
    relevance_score: float = 0.0


class ComprehensiveURLDiscovery:
    """Discovers ALL relevant URLs across multiple categories."""

    # Category definitions
    CATEGORIES = {
        "social": "Social Media Profiles",
        "thought_leadership": "Blogs, Articles & Speaking",
        "financial": "SEC Filings & Financial Reports",
        "technical": "GitHub, Patents & Research",
        "news": "News Articles & Press Releases",
        "video": "YouTube & Video Content",
        "podcast": "Podcasts & Audio Interviews",
        "company_info": "Company Website & About Pages"
    }

    def __init__(self):
        self.discovered_urls: Set[str] = set()
        self.results: List[URLResult] = []
        self.company_domain: str = None

    def discover(self, company: str, person: str = None, max_urls: int = 100) -> List[URLResult]:
        """
        Comprehensive URL discovery across all categories.

        Args:
            company: Company name
            person: Person name (optional)
            max_urls: Maximum URLs to return

        Returns:
            List of URLResult objects, sorted by category and relevance
        """
        logger.info(f"🚀 Starting comprehensive URL discovery for {company}" +
                   (f" / {person}" if person else ""))

        # Find company website first
        self.company_domain = self._find_company_website(company)
        logger.info(f"📍 Company domain: {self.company_domain}")

        # Discover URLs by category (parallel would be better, but sequential for clarity)
        self._discover_social_profiles(company, person)
        self._discover_thought_leadership(company, person)
        self._discover_financial_info(company)
        self._discover_technical_content(company, person)
        self._discover_news_media(company, person)
        self._discover_video_content(company, person)
        self._discover_podcast_content(company, person)
        self._discover_company_info(company)

        # Post-processing
        self._deduplicate_urls()
        self._score_relevance(company, person)

        # Sort and limit
        sorted_results = sorted(self.results, key=lambda x: x.relevance_score, reverse=True)
        top_results = sorted_results[:max_urls]

        logger.info(f"✓ Discovered {len(self.discovered_urls)} URLs, returning top {len(top_results)}")
        self._log_category_breakdown(top_results)

        return top_results

    # =============================================================================
    # CATEGORY 1: SOCIAL MEDIA PROFILES
    # =============================================================================

    def _discover_social_profiles(self, company: str, person: str = None):
        """Discover social media profiles across all major platforms."""
        logger.info("🔍 Discovering social media profiles...")

        platforms = {
            "linkedin.com": f"{person or company} LinkedIn",
            "twitter.com": f"{person or company} Twitter",
            "facebook.com": f"{company} Facebook",
            "instagram.com": f"{company} Instagram",
            "youtube.com": f"{company} YouTube channel",
            "github.com": f"{company} GitHub",
            "medium.com": f"{person or company} Medium"
        }

        for platform, query in platforms.items():
            self._google_search(
                query=query,
                category="social",
                num_results=3,
                site=platform
            )

    # =============================================================================
    # CATEGORY 2: THOUGHT LEADERSHIP
    # =============================================================================

    def _discover_thought_leadership(self, company: str, person: str = None):
        """Discover blog posts, articles, interviews, and speaking engagements."""
        logger.info("🔍 Discovering thought leadership content...")

        if person:
            queries = [
                f"{person} interview",
                f"{person} article",
                f"{person} blog post",
                f"{person} speaking",
                f"{person} conference talk",
                f"{person} podcast guest",
                f"{person} {company} insights",
                f"{person} writes about"
            ]
        else:
            queries = [
                f"{company} blog",
                f"{company} insights",
                f"{company} thought leadership",
                f"{company} articles"
            ]

        for query in queries:
            self._google_search(query, "thought_leadership", num_results=5)

        # Check specific platforms
        platforms = ["medium.com", "substack.com", "dev.to", "hashnode.com"]
        for platform in platforms:
            self._google_search(
                f"{person or company} {platform}",
                "thought_leadership",
                num_results=3,
                site=platform
            )

    # =============================================================================
    # CATEGORY 3: FINANCIAL INFORMATION
    # =============================================================================

    def _discover_financial_info(self, company: str):
        """Discover SEC filings, investor relations, earnings transcripts."""
        logger.info("🔍 Discovering financial information...")

        # SEC Filings (direct link)
        try:
            filing_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={company.replace(' ', '+')}&action=getcompany&type=&dateb=&owner=exclude&count=40"
            self.results.append(URLResult(
                url=filing_url,
                title=f"{company} SEC EDGAR Filings",
                snippet="Official SEC filings including 10-K, 10-Q, 8-K",
                category="financial"
            ))
            self.discovered_urls.add(filing_url)
        except Exception as e:
            logger.warning(f"SEC filing link error: {e}")

        # Search for investor relations
        queries = [
            f"{company} investor relations",
            f"{company} earnings transcript",
            f"{company} annual report",
            f"{company} quarterly results",
            f"{company} financial statements"
        ]

        for query in queries:
            self._google_search(query, "financial", num_results=3)

    # =============================================================================
    # CATEGORY 4: TECHNICAL CONTENT
    # =============================================================================

    def _discover_technical_content(self, company: str, person: str = None):
        """Discover GitHub repos, patents, research papers, technical blogs."""
        logger.info("🔍 Discovering technical content...")

        # GitHub
        self._google_search(
            f"{company} GitHub",
            "technical",
            num_results=5,
            site="github.com"
        )

        # Patents
        self._google_search(
            f"{company} patents",
            "technical",
            num_results=5
        )

        # Research papers
        platforms = ["arxiv.org", "scholar.google.com", "papers.ssrn.com"]
        for platform in platforms:
            self._google_search(
                f"{person or company} {platform}",
                "technical",
                num_results=3,
                site=platform
            )

        # Technical blogs
        self._google_search(
            f"{company} engineering blog",
            "technical",
            num_results=5
        )
        self._google_search(
            f"{company} technical blog",
            "technical",
            num_results=5
        )

    # =============================================================================
    # CATEGORY 5: NEWS & MEDIA
    # =============================================================================

    def _discover_news_media(self, company: str, person: str = None):
        """Discover news articles, press releases, media mentions."""
        logger.info("🔍 Discovering news and media coverage...")

        queries = [
            f"{company} news",
            f"{company} press release",
            f"{company} announcement",
            f"{company} launches"
        ]

        if person:
            queries.extend([
                f"{person} {company} news",
                f"{person} interview",
                f"{person} profile"
            ])

        for query in queries:
            self._google_search(query, "news", num_results=5)

        # News sources
        news_sites = [
            "techcrunch.com", "bloomberg.com", "reuters.com",
            "wsj.com", "nytimes.com", "theverge.com", "wired.com"
        ]

        for site in news_sites:
            self._google_search(
                f"{company} {site}",
                "news",
                num_results=2,
                site=site
            )

    # =============================================================================
    # CATEGORY 6: VIDEO CONTENT
    # =============================================================================

    def _discover_video_content(self, company: str, person: str = None):
        """Discover YouTube videos, conference talks, video interviews."""
        logger.info("🔍 Discovering video content...")

        if YOUTUBE_API_KEY:
            self._youtube_search(company, person)
        else:
            # Fallback to Google search
            queries = [
                f"{company} YouTube",
                f"{person} video interview" if person else f"{company} video",
                f"{person} talk" if person else f"{company} presentation"
            ]

            for query in queries:
                self._google_search(query, "video", num_results=5, site="youtube.com")

    def _youtube_search(self, company: str, person: str = None):
        """Search YouTube API for videos."""
        try:
            queries = [f"{company} official"]
            if person:
                queries.extend([
                    f"{person} interview",
                    f"{person} talk",
                    f"{person} {company}"
                ])

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

                    if video_url not in self.discovered_urls:
                        self.results.append(URLResult(
                            url=video_url,
                            title=item["snippet"]["title"],
                            snippet=item["snippet"]["description"][:200],
                            category="video"
                        ))
                        self.discovered_urls.add(video_url)

            logger.info(f"YouTube: Found {len([r for r in self.results if r.category == 'video'])} videos")

        except Exception as e:
            logger.warning(f"YouTube search error: {e}")

    # =============================================================================
    # CATEGORY 7: PODCAST CONTENT
    # =============================================================================

    def _discover_podcast_content(self, company: str, person: str = None):
        """Discover podcast episodes featuring the person/company."""
        logger.info("🔍 Discovering podcast content...")

        if not person:
            return  # Podcasts are usually person-focused

        queries = [
            f"{person} podcast",
            f"{person} interview podcast",
            f"{person} guest",
        ]

        for query in queries:
            # Search Spotify
            self._google_search(
                query,
                "podcast",
                num_results=5,
                site="open.spotify.com"
            )

            # Search Apple Podcasts
            self._google_search(
                query,
                "podcast",
                num_results=5,
                site="podcasts.apple.com"
            )

    # =============================================================================
    # CATEGORY 8: COMPANY INFORMATION
    # =============================================================================

    def _discover_company_info(self, company: str):
        """Discover company website pages: about, team, products, etc."""
        logger.info("🔍 Discovering company information pages...")

        if self.company_domain:
            # Parse sitemap for all company pages
            self._discover_sitemap(self.company_domain, company)

        # Search for specific company pages
        pages = ["about", "team", "leadership", "careers", "products", "services", "contact", "press"]

        for page in pages:
            self._google_search(
                f"{company} {page}",
                "company_info",
                num_results=2,
                site=self.company_domain
            )

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

                    root = ET.fromstring(response.content)
                    namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                    urls = root.findall(".//ns:loc", namespaces)

                    for url_elem in urls[:50]:  # Limit to first 50 pages
                        page_url = url_elem.text

                        if self._is_relevant_page(page_url):
                            self.results.append(URLResult(
                                url=page_url,
                                title=f"{company} - {self._extract_page_title(page_url)}",
                                snippet="Company website page",
                                category="company_info"
                            ))
                            self.discovered_urls.add(page_url)

                    logger.info(f"Sitemap: Found {len([r for r in self.results if r.category == 'company_info'])} pages")
                    break

                except requests.RequestException:
                    continue

        except Exception as e:
            logger.warning(f"Sitemap parsing error: {e}")

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    def _find_company_website(self, company: str) -> str:
        """Find the official company website domain."""
        if not GOOGLE_SEARCH_API_KEY:
            return None

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
                domain = urlparse(website_url).netloc.replace("www.", "")
                return domain

        except Exception as e:
            logger.warning(f"Could not find company website: {e}")

        return None

    def _google_search(self, query: str, category: str, num_results: int = 10, site: str = None):
        """Perform Google Custom Search."""
        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            logger.warning("Google Search API not configured")
            return

        try:
            # Add site restriction if specified
            if site:
                query = f"{query} site:{site}"

            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": GOOGLE_SEARCH_API_KEY,
                "cx": GOOGLE_SEARCH_ENGINE_ID,
                "q": query,
                "num": min(num_results, 10)  # API max is 10
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
            logger.warning(f"Google search error for '{query}': {e}")

    def _is_relevant_page(self, url: str) -> bool:
        """Filter relevant company website pages."""
        relevant_keywords = [
            "about", "team", "leadership", "company", "mission", "vision",
            "product", "service", "technology", "innovation", "solution",
            "blog", "news", "press", "media", "contact", "career", "culture"
        ]

        irrelevant_patterns = [
            r"\?page=\d+", r"/search", r"/category/", r"/tag/",
            r"/author/", r"/\d{4}/\d{2}/\d{2}/"
        ]

        url_lower = url.lower()

        has_relevant = any(keyword in url_lower for keyword in relevant_keywords)
        is_irrelevant = any(re.search(pattern, url) for pattern in irrelevant_patterns)

        return has_relevant and not is_irrelevant

    def _extract_page_title(self, url: str) -> str:
        """Extract readable title from URL path."""
        path = urlparse(url).path
        segments = [s for s in path.split("/") if s]

        if segments:
            title = segments[-1].replace("-", " ").replace("_", " ").title()
            return title

        return "Homepage"

    def _deduplicate_urls(self):
        """Remove duplicate URLs."""
        seen = set()
        unique_results = []

        for result in self.results:
            normalized = self._normalize_url(result.url)

            if normalized not in seen:
                seen.add(normalized)
                result.url = normalized
                unique_results.append(result)

        self.results = unique_results
        logger.info(f"Deduplication: {len(self.results)} unique URLs")

    def _normalize_url(self, url: str) -> str:
        """Normalize URL (remove tracking params, fragments)."""
        parsed = urlparse(url)

        query_params = parse_qs(parsed.query)
        tracking_params = [
            "utm_source", "utm_medium", "utm_campaign", "utm_content",
            "utm_term", "ref", "source", "fbclid", "gclid"
        ]

        cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}
        cleaned_query = urlencode(cleaned_params, doseq=True)

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
        """Score each URL's relevance."""
        company_terms = company.lower().split()
        person_terms = person.lower().split() if person else []

        for result in self.results:
            score = 0.0
            text = f"{result.title} {result.snippet}".lower()

            # Company/person mentions
            for term in company_terms:
                score += text.count(term) * 2
            for term in person_terms:
                score += text.count(term) * 3

            # Category priority
            category_scores = {
                "company_info": 10,
                "social": 9,
                "thought_leadership": 8,
                "financial": 8,
                "video": 7,
                "news": 6,
                "technical": 6,
                "podcast": 5
            }
            score += category_scores.get(result.category, 1)

            result.relevance_score = score

    def _log_category_breakdown(self, results: List[URLResult]):
        """Log category breakdown for debugging."""
        category_counts = {}
        for result in results:
            category_counts[result.category] = category_counts.get(result.category, 0) + 1

        logger.info("Category breakdown:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {category}: {count} URLs")


def discover_urls(company: str, person: str = None, max_urls: int = 100) -> List[Dict[str, Any]]:
    """
    Main entry point for comprehensive URL discovery.

    Args:
        company: Company name
        person: Person name (optional)
        max_urls: Maximum URLs to return

    Returns:
        List of dicts with url, title, snippet, category, score
    """
    discoverer = ComprehensiveURLDiscovery()
    results = discoverer.discover(company, person, max_urls)

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
