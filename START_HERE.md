# 🚀 START HERE - Interview Knowledge Base

Welcome! You're 2 commands away from using the system.

## ⚡ Quick Start (30 seconds)

```bash
# 1. Start the UI
./start_ui.sh

# 2. Open browser to http://localhost:8000
```

That's it! The UI is ready to use.

## 📝 Your First Brief (2 minutes)

1. **Enter a company:**
   - Type: `OpenAI`
   - Leave person blank or add `Sam Altman`

2. **Click "RUN_PIPELINE"**
   - Watch the terminal console fill with progress
   - Takes ~60 seconds for first run

3. **Read the brief:**
   - Scroll down to see the generated summary
   - Check insights, entities, citations

4. **Ask questions in chat:**
   - Type: `What are OpenAI's main products?`
   - Get RAG-powered answers with citations

## 🎯 What Just Happened?

### Step 1: Ingestion (~30 sec)
The system fetched data from 5 sources:
- SEC filings (10-K, 10-Q reports)
- PubMed research articles
- ClinicalTrials.gov studies
- Google Patents
- YouTube transcripts

### Step 2: Indexing (~20 sec)
Processed the data:
- Generated embeddings (OpenAI text-embedding-3-large)
- Extracted entities (spaCy NER)
- Clustered content (adaptive KMeans)
- Cached everything for future use

### Step 3: Generation (~10 sec)
Created your brief:
- Retrieved relevant chunks
- Fed to GPT-4o (or Claude)
- Extracted insights and citations
- Returned structured JSON

## 💡 Next Steps

### Try Different Modes
```bash
# In the UI, change the "BRIEF_MODE" dropdown:
- summary      → General overview
- technical    → Patents, innovations
- biographical → Person's background
- strategic    → Business strategy
```

### Iterate Faster
After first run, check the boxes:
- ☑️ SKIP_INGESTION
- ☑️ SKIP_INDEXING

Then change mode and re-run. Takes 2 seconds!

### Use the Chat
Ask follow-up questions:
- "What are their key innovations?"
- "Tell me about their leadership team"
- "What's their market position?"

All answers are RAG-powered with citations.

## 📊 What You Have

Your `.env` file already has all API keys configured:
- ✅ OpenAI (required)
- ✅ Anthropic (optional, for Claude)
- ✅ SerpAPI (for patents)
- ✅ PubMed (for research)
- ✅ YouTube (for videos)

## 🎨 UI Features

- **Real-time progress** - Watch each step complete
- **RAG chat** - Ask questions, get cited answers
- **File browser** - See what was ingested
- **Auto-save** - Remembers your last company
- **Beautiful design** - Retro terminal aesthetic

## 💰 Cost

- First brief: ~$0.18
- Subsequent briefs: ~$0.05 (embeddings cached)
- Chat queries: ~$0.01 each

Very affordable for interview prep!

## 🔧 Troubleshooting

**UI won't start?**
```bash
pip install fastapi uvicorn
cd ui && python app.py
```

**OpenAI API error?**
- Check your API key in `.env`
- Verify credits: https://platform.openai.com/usage

**Want to use CLI instead?**
```bash
python main.py --company "OpenAI" --person "Sam Altman"
```

## 📚 Learn More

- **QUICKSTART.md** - Detailed examples
- **README.md** - Full documentation
- **SYSTEM_SUMMARY.md** - Architecture deep-dive
- **ui/README.md** - UI documentation

## 🎉 You're Ready!

The system is production-ready. Just run `./start_ui.sh` and start researching!

---

**Questions?** Check the docs or just experiment. The UI is intuitive and safe to explore.

**Happy researching!** 🚀
