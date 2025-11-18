# COMPREHENSIVE IMPROVEMENTS GUIDE

## 🚀 TIER 1: Add More Data Sources (3-5x URLs)

### Quick Wins (No API Key Required)

```python
# Already implemented in enhanced_discovery.py:

1. Reddit API - Discussions, AMAs (FREE)
2. Hacker News Algolia - Tech discussions (FREE)
3. Semantic Scholar - 200M papers (FREE)
4. Medium via Google - Articles (FREE if using Google Search)
```

### Premium APIs (High Impact, Low Cost)

```python
# Add to config.py:

NEWSAPI_KEY=xxx           # $449/month for 250k requests (or FREE 100/day)
LISTENNOTES_API_KEY=xxx   # $49/month for 1000 requests
TWITTER_BEARER_TOKEN=xxx  # $100/month for Essential access
CRUNCHBASE_API_KEY=xxx    # $29/month for Basic
```

**Expected Impact:**
- Reddit: +20-30 URLs (discussions, AMAs)
- Hacker News: +15-25 URLs (tech discussions)
- NewsAPI: +50-80 URLs (comprehensive news)
- Listen Notes: +10-20 URLs (podcast episodes)
- Twitter: +5-10 URLs (profiles, threads)
- Semantic Scholar: +20-40 URLs (academic papers)

**Total: 120-205 additional URLs = 2-3x current output**

---

## ⚡ TIER 2: Performance Improvements (5-10x Faster)

### 1. Parallel API Calls

**Current:** Sequential (30-60 seconds)
**After:** Parallel (5-10 seconds)

```python
# Replace in url_discovery.py:

import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelURLDiscovery:
    def discover(self, company: str, person: str = None):
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(self._discover_social_profiles, company, person),
                executor.submit(self._discover_thought_leadership, company, person),
                executor.submit(self._discover_financial_info, company),
                executor.submit(self._discover_technical_content, company, person),
                executor.submit(self._discover_news_media, company, person),
                executor.submit(self._discover_video_content, company, person),
                executor.submit(self._discover_podcast_content, company, person),
                executor.submit(self._discover_company_info, company),
            ]

            # Wait for all to complete
            for future in futures:
                future.result()

        return self.results
```

**Expected Impact:** 5-10x faster discovery

### 2. Redis Caching

**Problem:** Re-discovering same company wastes API calls
**Solution:** Cache for 24 hours

```python
# Add to requirements.txt:
redis==5.0.0

# Add caching layer:
import redis
import json
import hashlib

class CachedURLDiscovery:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0)

    def discover(self, company: str, person: str = None, max_urls: int = 100):
        # Generate cache key
        cache_key = hashlib.md5(f"{company}:{person}:{max_urls}".encode()).hexdigest()

        # Check cache
        cached = self.redis.get(cache_key)
        if cached:
            logger.info(f"✓ Cache hit for {company}")
            return json.loads(cached)

        # Run discovery
        results = self._run_discovery(company, person, max_urls)

        # Cache for 24 hours
        self.redis.setex(cache_key, 86400, json.dumps(results))

        return results
```

**Expected Impact:**
- Free re-runs within 24 hours
- 100x faster for cached requests

### 3. Rate Limiting with Backoff

**Problem:** API rate limits cause failures
**Solution:** Smart retry with exponential backoff

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.HTTPError as e:
                    if e.response.status_code == 429:  # Rate limit
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limited, retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        raise
            raise Exception(f"Failed after {max_retries} retries")
        return wrapper
    return decorator

# Apply to API calls:
@retry_with_backoff(max_retries=3)
def _google_search(self, query: str, category: str):
    # ... existing code ...
```

**Expected Impact:**
- 95%+ success rate even with rate limits
- Automatic recovery from temporary failures

---

## 🎯 TIER 3: Quality Improvements (2-3x Better Results)

### 1. AI-Powered Relevance Scoring

**Problem:** Keyword matching misses context
**Solution:** Use Claude/GPT to score relevance

```python
import anthropic

def score_url_relevance(url_data: dict, company: str, person: str) -> float:
    """
    Use Claude to score URL relevance (0-10).
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""
    Score the relevance of this URL for researching {person} at {company} (0-10):

    Title: {url_data['title']}
    Snippet: {url_data['snippet']}
    URL: {url_data['url']}

    Consider:
    - Direct mention of person/company
    - Content quality (primary vs secondary source)
    - Recency and authority
    - Usefulness for interview prep

    Return only a number 0-10.
    """

    response = client.messages.create(
        model="claude-3-haiku-20240307",  # Fast & cheap
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}]
    )

    return float(response.content[0].text.strip())

# Apply after discovery:
for url in results:
    url['ai_score'] = score_url_relevance(url, company, person)

# Re-rank by AI score
results.sort(key=lambda x: x['ai_score'], reverse=True)
```

**Expected Impact:**
- 60-80% improvement in top results quality
- Filters out low-quality/spam URLs
- Cost: ~$0.02 per 100 URLs (Haiku)

### 2. Content Quality Filtering

**Problem:** Spam sites, low-quality blogs
**Solution:** Domain reputation scoring

```python
# Known high-quality domains (bonus scoring)
HIGH_QUALITY_DOMAINS = {
    # News
    "bloomberg.com": 10,
    "reuters.com": 10,
    "wsj.com": 10,
    "nytimes.com": 9,
    "techcrunch.com": 8,

    # Professional
    "linkedin.com": 9,
    "github.com": 9,
    "medium.com": 7,

    # Academic
    "arxiv.org": 10,
    "scholar.google.com": 10,
    "semanticscholar.org": 9,

    # Company
    "sec.gov": 10,
    "crunchbase.com": 9,
}

# Low-quality patterns (filter out)
SPAM_PATTERNS = [
    r"clickbait",
    r"get-rich",
    r"download-now",
    r"/ads/",
    r"sponsored-content"
]

def is_quality_url(url: str, title: str) -> bool:
    """Filter spam/low-quality URLs."""
    domain = urlparse(url).netloc

    # Check spam patterns
    if any(re.search(pattern, url.lower() + title.lower()) for pattern in SPAM_PATTERNS):
        return False

    # Check if high-quality domain
    if any(domain.endswith(hq_domain) for hq_domain in HIGH_QUALITY_DOMAINS):
        return True

    return True  # Allow by default
```

### 3. Freshness Scoring

**Problem:** Old content ranks same as new
**Solution:** Extract dates, boost recent content

```python
from datetime import datetime
import dateutil.parser

def extract_publish_date(url: str, snippet: str) -> datetime:
    """
    Extract publish date from snippet or URL.
    """
    # Try common date patterns in snippet
    date_patterns = [
        r"(\d{4}-\d{2}-\d{2})",  # 2024-01-15
        r"(\w+ \d{1,2}, \d{4})",  # January 15, 2024
    ]

    for pattern in date_patterns:
        match = re.search(pattern, snippet)
        if match:
            try:
                return dateutil.parser.parse(match.group(1))
            except:
                pass

    return None

def calculate_freshness_score(date: datetime) -> float:
    """
    Score freshness (0-10).
    10 = published in last month
    5 = published in last year
    1 = published >3 years ago
    """
    if not date:
        return 5  # Unknown = neutral

    days_old = (datetime.now() - date).days

    if days_old < 30:
        return 10
    elif days_old < 90:
        return 9
    elif days_old < 180:
        return 8
    elif days_old < 365:
        return 7
    elif days_old < 730:
        return 5
    else:
        return max(1, 5 - (days_old / 365))
```

---

## 🧠 TIER 4: Advanced Features

### 1. Auto-Discovery of Related People

```python
def discover_related_people(company: str) -> List[str]:
    """
    Use AI to find related people at company.
    """
    client = anthropic.Anthropic()

    prompt = f"""
    List the top 10 most important people at {company} for interview research.
    Include CEO, founders, executives, prominent engineers.

    Return ONLY a JSON array of names:
    ["Name 1", "Name 2", ...]
    """

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.content[0].text)

# Then discover URLs for each person:
people = discover_related_people("Anthropic")
for person in people:
    discover_urls(company="Anthropic", person=person)
```

### 2. Timeline View

```python
def organize_by_timeline(urls: List[dict]) -> dict:
    """
    Organize URLs by publication date.
    """
    timeline = {
        "last_week": [],
        "last_month": [],
        "last_quarter": [],
        "last_year": [],
        "older": []
    }

    for url in urls:
        date = extract_publish_date(url['url'], url['snippet'])
        if not date:
            timeline["older"].append(url)
            continue

        days_old = (datetime.now() - date).days

        if days_old <= 7:
            timeline["last_week"].append(url)
        elif days_old <= 30:
            timeline["last_month"].append(url)
        elif days_old <= 90:
            timeline["last_quarter"].append(url)
        elif days_old <= 365:
            timeline["last_year"].append(url)
        else:
            timeline["older"].append(url)

    return timeline
```

### 3. Sentiment Analysis

```python
def analyze_sentiment(urls: List[dict], company: str) -> dict:
    """
    Categorize URLs by sentiment (positive, neutral, negative).
    """
    categories = {"positive": [], "neutral": [], "negative": []}

    for url in urls:
        prompt = f"""
        Analyze sentiment of this article about {company}:
        Title: {url['title']}
        Snippet: {url['snippet']}

        Return ONLY: positive, neutral, or negative
        """

        # Use Claude Haiku for speed
        sentiment = get_ai_response(prompt).strip().lower()
        categories[sentiment].append(url)

    return categories
```

---

## 📊 SUMMARY: Expected Total Impact

| Improvement | Time | URL Increase | Quality | Speed |
|-------------|------|--------------|---------|-------|
| **Tier 1: More APIs** | 2-3 days | 3-5x (300-500) | +40% | Same |
| **Tier 2: Performance** | 1 day | Same | Same | 5-10x |
| **Tier 3: Quality** | 2 days | Same | +60% | Same |
| **Tier 4: Advanced** | 1 week | 2x | +30% | Same |

**Grand Total with All Tiers:**
- **500-800 URLs** per company/person (vs 100 now)
- **90%+ relevance** (vs 60% now)
- **5-10 seconds** discovery time (vs 30-60 now)
- **Cached repeats** are instant and free

---

## 🎯 RECOMMENDED IMPLEMENTATION ORDER

### Week 1: Quick Wins
1. Add Reddit API (1 hour)
2. Add Hacker News API (1 hour)
3. Add Semantic Scholar (1 hour)
4. Parallel processing (2 hours)

**Result:** 2x URLs, 5x faster

### Week 2: Premium APIs
1. Sign up for NewsAPI (30 min)
2. Integrate NewsAPI (2 hours)
3. Sign up for Listen Notes (30 min)
4. Integrate Listen Notes (2 hours)

**Result:** 3x URLs total

### Week 3: Quality
1. Implement caching (3 hours)
2. Add quality filtering (2 hours)
3. Add freshness scoring (2 hours)

**Result:** 60% better quality

### Week 4: Polish
1. AI relevance scoring (4 hours)
2. Timeline view (2 hours)
3. Related people discovery (2 hours)

**Result:** Production-ready comprehensive system

---

## 💰 COST ANALYSIS

### Free Tier (Current + Quick Wins)
- Google Search: 100/day free → ~2-5 companies/day
- YouTube: 10k units/day → 300+ companies/day
- Reddit: Free unlimited
- Hacker News: Free unlimited
- Semantic Scholar: Free unlimited

**Cost: $0**

### Paid Tier (All APIs)
- Google Search: $5/1000 searches → ~$0.25/company
- NewsAPI: $449/month → $0.002/company (at scale)
- Listen Notes: $49/month → $0.05/company
- Twitter: $100/month → $0.004/company
- Claude Haiku (scoring): ~$0.02/company

**Total: ~$0.33 per company** (assuming 1000 companies/month)

**ROI:**
- 500+ URLs vs manually finding them (10+ hours saved)
- Worth = $300-500 of research time saved
- ROI = 900-1500x

---

## 🚀 START HERE

Pick ONE improvement to start with:

**Option A: Most URLs** → Add NewsAPI + Reddit + HN (4 hours, +150 URLs)
**Option B: Best Quality** → Add AI scoring + filtering (6 hours, +60% quality)
**Option C: Fastest ROI** → Add parallel processing + caching (5 hours, 5x speed)

My recommendation: **Start with Option A** (most URLs), then B, then C.
