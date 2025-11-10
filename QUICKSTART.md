# Interview KB - Quick Start Guide

Get up and running with the Interview Knowledge Base in under 5 minutes.

## 🚀 Quick Setup

```bash
# 1. Install dependencies (one-time setup)
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 2. Your API keys are already configured in .env
# (Keys were moved from .env.example for security)

# 3. Start the web UI
./start_ui.sh
```

Then open your browser to **http://localhost:8000**

## 💡 First Run Example

### Using the Web UI

1. **Enter Company & Person:**
   - Company: `OpenAI`
   - Person: `Sam Altman`

2. **Select Mode:**
   - Choose `biographical` for career/background info
   - Or `technical` for innovations/patents
   - Or `summary` for general overview

3. **Click "RUN_PIPELINE"**
   - Watch real-time progress in the terminal console
   - Ingestion: ~30 seconds (fetches from 5 APIs)
   - Indexing: ~20 seconds (embeddings + clustering)
   - Generation: ~10 seconds (GPT-4o brief)

4. **Read the Generated Brief**
   - Scroll down to see structured summary
   - View key entities and insights
   - Check citations and metadata

5. **Ask Questions in Chat**
   - Type: "What are OpenAI's key products?"
   - Or: "Tell me about Sam Altman's background"
   - Get RAG-powered answers with citations

### Using the CLI

```bash
# Run full pipeline
python main.py --company "OpenAI" --person "Sam Altman" --mode biographical

# Re-generate brief with existing data (faster)
python main.py --company "OpenAI" --skip-ingestion --skip-indexing --mode technical

# Try Claude instead of GPT-4o
python main.py --company "OpenAI" --model claude-3-5-sonnet-20241022 --skip-ingestion --skip-indexing
```

## 📂 What Gets Created

After running the pipeline for "OpenAI":

```
data/
├── raw/
│   └── openai/
│       └── source.jsonl           # ~150 documents from 5 APIs
└── index/
    └── openai/
        ├── embeddings.npy          # 3072-dim vectors
        ├── entities.jsonl          # NER extractions
        ├── clusters.json           # KMeans clusters
        ├── metadata.json           # Index info
        └── embedding_cache.json    # SHA256 cache
```

## 🎯 Different Use Cases

### 1. Interview Prep
```bash
python main.py --company "Google" --person "Sundar Pichai" --mode biographical
```
Get background on the person you're meeting.

### 2. Technical Research
```bash
python main.py --company "Anthropic" --mode technical
```
Deep dive into patents, innovations, technical capabilities.

### 3. Strategic Analysis
```bash
python main.py --company "Tesla" --mode strategic
```
Understand business strategy, market position, vision.

### 4. Quick Summary
```bash
python main.py --company "Stripe" --mode summary --skip-ingestion --skip-indexing
```
Generate a new brief from existing data (2 seconds).

## 🔧 Troubleshooting

### "No module named 'spacy'"
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

### "OpenAI API error"
- Check your API key in `.env`
- Verify you have credits at https://platform.openai.com/usage

### "Index not found"
- Run ingestion + indexing first (don't use skip flags)
- Or check that `data/index/{company}/` exists

### UI won't start
```bash
pip install fastapi uvicorn
cd ui && python app.py
```

## 💰 Cost Estimates

**First run** (1000 chunks):
- Embedding: $0.13 (text-embedding-3-large)
- Generation: $0.05 (GPT-4o)
- **Total: ~$0.18**

**Subsequent runs** (cached embeddings):
- Generation only: $0.05
- **Total: ~$0.05**

## 🎨 UI Features

The retro web interface includes:

- **Real-time streaming** - Watch pipeline progress live
- **RAG chat** - Ask questions about indexed data
- **File browser** - See what was ingested
- **Auto-save** - Remembers your last company/person
- **Beautiful design** - Retro terminal aesthetic

## 📚 Next Steps

1. **Try different companies:**
   - Tech: OpenAI, Anthropic, Google, Meta
   - Biotech: Moderna, Genentech
   - Finance: Stripe, Square

2. **Experiment with modes:**
   - `summary` - General overview
   - `technical` - Deep technical dive
   - `biographical` - Person-focused
   - `strategic` - Business strategy

3. **Compare models:**
   - GPT-4o: Faster, cheaper
   - Claude 3.5 Sonnet: More nuanced

4. **Use the chat:**
   - Ask follow-up questions
   - Explore specific aspects
   - Get cited answers

## 🚀 Pro Tips

1. **Skip flags for iteration:**
   ```bash
   # First run: full pipeline
   python main.py --company "X"

   # Then iterate on modes:
   python main.py --company "X" --mode technical --skip-ingestion --skip-indexing
   python main.py --company "X" --mode strategic --skip-ingestion --skip-indexing
   ```

2. **Save outputs:**
   ```bash
   python main.py --company "X" --output brief.json
   ```

3. **Use verbose logging:**
   ```bash
   python main.py --company "X" --verbose
   ```

4. **Web UI persistence:**
   - UI auto-saves your last company/person
   - Just reload the page to resume

---

**Happy researching!** 🎉

For more details, see [README.md](README.md) or [ui/README.md](ui/README.md).
