# URL Discovery Mode - Quick Guide

## 🎯 What Is This?

The **primary mode** of Interview KB - discovers all relevant URLs for a company/person and formats them for direct NotebookLM import.

## 🚀 Quick Start (30 seconds)

1. **Start the UI:**
   ```bash
   ./start_ui.sh
   # Open http://localhost:8000
   ```

2. **Switch to URL Discovery:**
   - Click the **"URL_DISCOVERY"** tab in the UI

3. **Enter details:**
   - Company: `OpenAI`
   - Person: `Sam Altman` (optional)

4. **Click "DISCOVER_URLS"**
   - Wait ~10 seconds
   - See 30-50 relevant URLs

5. **Copy for NotebookLM:**
   - Click **"COPY_ALL"** button
   - Paste into NotebookLM
   - Done!

## 📋 What URLs Are Discovered?

The system searches across:

### 1. Company Website
- Homepage
- About/Team/Leadership pages
- Product/Service pages
- Blog/News/Press releases
- **All subpages from sitemap.xml**

### 2. SEC Filings
- Direct links to company's SEC EDGAR page
- 10-K, 10-Q filings
- Recent annual reports

### 3. YouTube
- Company official channel
- Interview videos
- Conference talks
- Product demos

### 4. Podcasts
- Spotify episodes
- Apple Podcasts
- Interview appearances

### 5. News Articles
- Recent news coverage
- Press releases
- Industry publications

### 6. Research
- Patents (via Google)
- Academic papers
- Technical blogs

## 🔍 How It Works

**Smart Discovery Pipeline:**
```
1. Google Custom Search API → General web results
2. Company Website → Parse sitemap.xml for all subpages
3. SEC EDGAR → Direct filing links
4. YouTube Data API → Video search
5. Spotify/Apple → Podcast search
6. News APIs → Recent articles

↓

Smart Filtering & Ranking:
- Remove duplicates
- Score by relevance
- Filter out ads/irrelevant pages
- Prioritize authoritative sources

↓

Output (newline-separated):
https://company.com/about
https://company.com/team
https://youtube.com/watch?v=xyz
...
```

## 📊 Output Format

**Perfect for NotebookLM:**
- One URL per line
- No commas or extra formatting
- Max 50 URLs (NotebookLM limit)
- Sorted by relevance
- Grouped by category (for your review)

**Example Output:**
```
https://openai.com/about
https://openai.com/research
https://openai.com/blog
https://www.sec.gov/cgi-bin/browse-edgar?company=openai
https://youtube.com/watch?v=L_Guz73e6fw
https://youtube.com/watch?v=WHoWGNQRXb0
...
```

## 🎨 UI Features

### URL Display Panel
- **Text box**: All URLs (one per line)
- **Copy button**: One-click clipboard copy
- **Stats**: Total URLs, categories count
- **Category breakdown**: See URLs organized by type

### Categories Shown
- COMPANY_SITE
- SEC
- YOUTUBE
- PODCAST
- NEWS
- WEB

Each category shows:
- Number of URLs
- Top 5 URLs with titles
- Link preview

## ⚙️ Configuration

### Basic Settings
- **MAX_URLS**: Default 50 (NotebookLM limit)
  - Can increase to 100 if needed
  - Higher = more comprehensive, slower

### API Requirements
**Required:**
- `GOOGLE_SEARCH_API_KEY` (100 free/day, $5/1000 after)
- `GOOGLE_SEARCH_ENGINE_ID`

**Optional (improves results):**
- `YOUTUBE_API_KEY` - More video results
- `SERPAPI_KEY` - Patent search

See [GOOGLE_SEARCH_SETUP.md](GOOGLE_SEARCH_SETUP.md) for setup instructions.

## 💡 Pro Tips

### 1. Include Person Name
```
Company: OpenAI
Person: Sam Altman
```
Gets better interview/biography URLs.

### 2. Review Categories
Before copying, check the category breakdown to see what was found.

### 3. Adjust MAX_URLS
- 50 URLs: Good balance (default)
- 30 URLs: Faster, most relevant only
- 100 URLs: Maximum coverage

### 4. Fallback Without Google Search
Even without Google Search API, you get:
- Company sitemap URLs
- SEC filings
- YouTube videos (if YOUTUBE_API_KEY set)

## 📈 Performance

- **Speed**: ~10 seconds per company
- **Cost**: ~$0.05 per company (with Google Search API)
- **Free tier**: 10-20 companies/day

## 🔧 Troubleshooting

### "No URLs found"
- Check company name spelling
- Try adding person name
- Verify Google Search API key in .env

### "API quota exceeded"
- You've used 100 free queries today
- Either wait until tomorrow or upgrade

### "Search engine not found"
- Check GOOGLE_SEARCH_ENGINE_ID in .env
- See [GOOGLE_SEARCH_SETUP.md](GOOGLE_SEARCH_SETUP.md)

### Not finding company website subpages
- Some sites don't have sitemap.xml
- System falls back to main pages only

## 🆚 vs. Full RAG Mode

| Feature | URL Discovery | Full RAG |
|---------|--------------|----------|
| **Speed** | 10 seconds | 60 seconds |
| **Output** | URLs for NotebookLM | Generated brief |
| **Cost** | $0.05 | $0.18 |
| **Use case** | Research prep | Interview prep |
| **APIs needed** | Google Search | OpenAI + all sources |

**When to use URL Discovery:**
- You want to use NotebookLM for research
- Quick URL gathering
- Need primary sources
- Budget-conscious

**When to use Full RAG:**
- You want AI-generated brief
- Chat Q&A capability
- Structured insights
- Direct consumption

## 📝 Example Use Cases

### 1. Interview Prep
```
Company: Stripe
Person: Patrick Collison
→ Get 50 URLs
→ Paste into NotebookLM
→ Ask: "What should I know about Patrick?"
```

### 2. Company Research
```
Company: Anthropic
→ Get company URLs
→ Review categories
→ Copy relevant sections to NotebookLM
```

### 3. Competitive Analysis
```
Run for multiple companies:
- OpenAI
- Anthropic
- Cohere
→ Compare URLs
→ See coverage differences
```

## 🎉 Quick Wins

**Best results with:**
- Large public companies (more online presence)
- Tech companies (more content)
- Public figures (more interviews/articles)

**May have limited results for:**
- Private companies
- Stealth startups
- International companies (English bias)

---

**Ready to try?** Just run `./start_ui.sh` and click the "URL_DISCOVERY" tab!
