# Google Custom Search API Setup

To use the URL Discovery mode, you need to set up Google Custom Search API (100 free queries/day).

## Step 1: Get API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Custom Search API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Custom Search API"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy your API key

## Step 2: Create Custom Search Engine

1. Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/controlpanel/create)
2. Configure your search engine:
   - **Sites to search:** Leave blank or add "*" to search the entire web
   - **Name:** Interview KB Search
   - **Language:** English
3. Click "Create"
4. Go to "Edit search engine" > "Setup"
5. Enable "Search the entire web"
6. Copy your **Search engine ID** (looks like: `abc123def456...`)

## Step 3: Add to .env File

```bash
# Add these lines to your .env file:
GOOGLE_SEARCH_API_KEY=your_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

## Usage Limits

**Free Tier:**
- 100 queries per day
- $5 per 1000 queries after that

**URL Discovery Usage:**
- Each company search uses ~5-10 queries
- So you can research ~10-20 companies per day for free

## Alternative: Skip Google Search

If you don't want to set up Google Search, the system will still work with:
- Direct SEC filings URLs
- YouTube videos (requires YOUTUBE_API_KEY)
- Company sitemaps

Just leave GOOGLE_SEARCH_API_KEY empty in .env.

## Testing

```bash
# Start UI
./start_ui.sh

# In browser:
1. Enter company: "OpenAI"
2. Click "URL_DISCOVERY" tab
3. Click "DISCOVER_URLS"
4. You should see 30-50 URLs
```

If you see errors, check:
- API key is correct in .env
- Custom Search API is enabled in Google Cloud
- Search engine ID is correct
- You haven't exceeded daily quota (100 queries)

## Troubleshooting

**Error: "API key not valid"**
- Double-check your API key in .env
- Make sure Custom Search API is enabled in Google Cloud Console

**Error: "Search engine not found"**
- Verify your Search engine ID
- Make sure "Search the entire web" is enabled in search engine settings

**No results found:**
- Some companies may have limited online presence
- Try adding a person name for better results
- Check that search queries are being constructed correctly (see console logs)

---

**Cost Estimate:**
If you research 100 companies in a month, that's ~1000 queries = $5 total. Very affordable!
