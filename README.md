# Interview Knowledge Base - URL Discovery Tool

**Comprehensive URL discovery for interview prep.** Input a person + company, get 100+ categorized URLs ready for NotebookLM.

## 🎯 What It Does

Discovers **every relevant URL** about a company/person across the web:

- **Social Media**: LinkedIn, Twitter, Facebook, Instagram, GitHub profiles
- **Thought Leadership**: Blog posts, articles, interviews, conference talks
- **Financial**: SEC filings, earnings transcripts, investor relations
- **Technical**: GitHub repos, patents, research papers, technical blogs
- **News/Media**: News articles, press releases, media mentions
- **Video**: YouTube videos, conference presentations
- **Podcasts**: Spotify, Apple Podcasts interviews
- **Company Info**: Official website, about pages, team pages, products

**Output**: Newline-separated URLs perfect for pasting into NotebookLM (or any research tool).

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Search API

**Required for comprehensive discovery:**

1. Go to [Google Custom Search](https://developers.google.com/custom-search)
2. Create a Custom Search Engine
3. Get your API key
4. Add to `.env` file:

```bash
GOOGLE_SEARCH_API_KEY=your_key_here
GOOGLE_SEARCH_ENGINE_ID=your_engine_id_here
```

**Optional (improves results):**
- `YOUTUBE_API_KEY` - Better video discovery
- `SERPAPI_KEY` - Patent search

### 3. Run Discovery

**Web UI (Recommended):**
```bash
./start_ui.sh
# Open http://localhost:8000
```

**CLI:**
```bash
python main.py --company "OpenAI" --person "Sam Altman"
```

## 📖 Usage

### Web Interface

1. Start the server: `./start_ui.sh`
2. Open `http://localhost:8000`
3. Enter:
   - Company: `OpenAI`
   - Person: `Sam Altman` (optional)
   - Max URLs: `100`
4. Click "DISCOVER_URLS"
5. Copy all URLs (one-click button)
6. Paste into NotebookLM

### Command Line

```bash
# Basic usage
python main.py --company "Stripe"

# With person name
python main.py --company "Stripe" --person "Patrick Collison"

# Get more URLs
python main.py --company "OpenAI" --max-urls 150

# Save to JSON
python main.py --company "Anthropic" --output urls.json
```

## 📊 Output Format

**Text (for NotebookLM):**
```
https://openai.com/about
https://linkedin.com/in/sam-altman
https://youtube.com/watch?v=xyz
...
```

**JSON:**
```json
{
  "company": "OpenAI",
  "person": "Sam Altman",
  "total_urls": 98,
  "urls": [
    {
      "url": "https://...",
      "title": "...",
      "snippet": "...",
      "category": "social",
      "score": 15.2
    }
  ],
  "by_category": {
    "social": [...],
    "thought_leadership": [...],
    ...
  }
}
```

## 🎯 How It Works

### Comprehensive Discovery Strategy

For **each category**, the tool:

1. **Social Media**
   - Searches LinkedIn, Twitter, Facebook, Instagram, GitHub, Medium
   - Finds both personal and company profiles
   - 3 results per platform

2. **Thought Leadership**
   - Searches for interviews, articles, blog posts
   - Checks Medium, Substack, dev.to, Hashnode
   - Conference talks, speaking engagements
   - ~40 results

3. **Financial**
   - Direct link to SEC EDGAR filings
   - Investor relations pages
   - Earnings transcripts, annual reports
   - ~15 results

4. **Technical**
   - GitHub repositories
   - Patent databases
   - arXiv, Google Scholar papers
   - Engineering/technical blogs
   - ~20 results

5. **News/Media**
   - General news searches
   - Targeted searches on TechCrunch, Bloomberg, WSJ, NYT, etc.
   - Press releases
   - ~25 results

6. **Video**
   - YouTube API search (if key provided)
   - Conference presentations
   - Video interviews
   - ~15 results

7. **Podcasts**
   - Spotify episode search
   - Apple Podcasts
   - Interview appearances
   - ~10 results

8. **Company Info**
   - Parses company sitemap.xml
   - About, team, leadership pages
   - Products, careers, press kit
   - ~20 results

**Total: 100+ URLs** across all categories, deduplicated and ranked by relevance.

## 🔧 Configuration

Edit `.env` file:

```bash
# REQUIRED
GOOGLE_SEARCH_API_KEY=your_key
GOOGLE_SEARCH_ENGINE_ID=your_id

# OPTIONAL (but recommended)
YOUTUBE_API_KEY=your_youtube_key

# OPTIONAL
SERPAPI_KEY=your_serpapi_key
```

## 💡 Tips

### Get Better Results

1. **Include person name** - Gets interviews, profiles, speaking engagements
2. **Use company full name** - "Anthropic PBC" better than "Anthropic"
3. **Increase max_urls** - Default 100, can go to 200+
4. **Review categories** - Check which categories found the most URLs

### API Costs

**Google Search API:**
- Free tier: 100 searches/day
- Paid: $5/1000 searches
- This tool uses ~20-50 searches per company
- Cost: ~$0.10-0.25 per company (paid tier)

**YouTube API:**
- Free tier: 10,000 units/day
- This tool uses ~30 units per company
- Essentially free for normal usage

## 📁 Project Structure

```
Interview-Knowledge-Base/
├── ingestion/
│   └── url_discovery.py      # Core URL discovery engine
├── ui/
│   ├── app.py                 # FastAPI backend
│   └── static/
│       ├── index.html         # Web UI
│       ├── app.js             # Frontend logic
│       └── styles.css         # Styling
├── main.py                    # CLI interface
├── config.py                  # Configuration
├── .env                       # API keys (create this)
├── .env.example               # Template
└── requirements.txt           # Dependencies
```

## 🚧 Troubleshooting

**"Google Search API not configured"**
- Add `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` to `.env`
- See [GOOGLE_SEARCH_SETUP.md](GOOGLE_SEARCH_SETUP.md) for setup guide

**"No URLs found"**
- Check company name spelling
- Try adding person name
- Verify API keys are correct

**"API quota exceeded"**
- You've used your free 100 searches today
- Wait until tomorrow or upgrade to paid tier

**Low number of URLs**
- Some companies have less online presence
- Private/stealth companies will have fewer results
- Add more API keys (YouTube, SerpAPI) for better coverage

## 🎯 Use Cases

### 1. Interview Preparation
```bash
# Get comprehensive research for your interview
python main.py --company "Stripe" --person "Patrick Collison" --output stripe.json
# → Paste URLs into NotebookLM
# → Ask: "What should I know about Patrick?"
```

### 2. Due Diligence
```bash
# Research a company before joining/investing
python main.py --company "Anthropic" --max-urls 150
# → Review financial docs, news, technical content
```

### 3. Competitive Analysis
```bash
# Compare multiple companies
python main.py --company "OpenAI" --output openai.json
python main.py --company "Anthropic" --output anthropic.json
python main.py --company "Cohere" --output cohere.json
# → Compare URL counts, categories, coverage
```

### 4. Sales/BD Research
```bash
# Research decision maker before a call
python main.py --company "Databricks" --person "Ali Ghodsi"
# → Get LinkedIn, recent interviews, thought leadership
```

## 🚀 What Makes This Comprehensive?

Unlike simple Google searches, this tool:

- ✅ **Searches 20+ sources** per company/person
- ✅ **8 distinct categories** with specialized queries
- ✅ **Parses sitemaps** to find ALL company pages
- ✅ **Deduplicates** and removes tracking parameters
- ✅ **Ranks by relevance** using smart scoring
- ✅ **API-driven** for consistent, reliable results
- ✅ **NotebookLM-ready** output format

**Result:** The most comprehensive URL list possible for interview prep.

## 📝 License

MIT License

## 🙏 Built With

- Google Custom Search API
- YouTube Data API
- FastAPI (Web UI)
- Python 3.8+

---

**Questions?** Check [GOOGLE_SEARCH_SETUP.md](GOOGLE_SEARCH_SETUP.md) for API setup help.
