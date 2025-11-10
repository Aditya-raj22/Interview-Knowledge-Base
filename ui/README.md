# Interview KB - Retro Web UI

A beautiful terminal-style web interface for the Interview Knowledge Base system.

## Design Philosophy

**Retro Terminal Aesthetic:**
- Vintage computing vibes with modern UX
- Cream (#FFFEF9) and white (#FFFFFF) base colors
- Crimson (#DC143C) for highlights and CTAs
- Monospace fonts (IBM Plex Mono, Courier Prime)
- Terminal-style console for pipeline progress
- Box shadows and crisp borders for depth

## Features

### 1. Real-Time Pipeline Execution
- Server-Sent Events (SSE) for live progress streaming
- Watch ingestion, indexing, and generation in real-time
- Terminal-style console output with colored status indicators

### 2. RAG Chat Interface
- Chatbot-style Q&A with context from indexed documents
- Citations displayed with each response
- Entity extraction showing key people, organizations, locations

### 3. File Browser
- View ingested documents by company
- Document counts and file sizes
- Preview capability (hover to see snippets)

### 4. Smart State Management
- Auto-save last company/person to localStorage
- Resume where you left off
- Skip flags for faster iteration

## Technology Stack

**Backend:**
- FastAPI (async Python web framework)
- Server-Sent Events for streaming
- CORS enabled for development

**Frontend:**
- Vanilla JavaScript (no framework overhead)
- CSS Grid for responsive layout
- Google Fonts (IBM Plex Mono, Courier Prime)

## Running the UI

```bash
# From project root
./start_ui.sh

# Or manually
cd ui
python app.py

# Open browser to http://localhost:8000
```

## API Endpoints

### POST /api/pipeline/stream
Stream pipeline execution progress via SSE.

**Request:**
```json
{
  "company": "OpenAI",
  "person": "Sam Altman",
  "mode": "summary",
  "model": "gpt-4o",
  "skip_ingestion": false,
  "skip_indexing": false
}
```

**Response:** SSE stream with events:
```
data: {"step": "ingestion", "status": "started", "message": "Fetching data..."}
data: {"step": "ingestion", "status": "completed", "message": "Data saved"}
data: {"step": "generation", "status": "completed", "brief": {...}}
```

### POST /api/chat
Execute a RAG query and get response.

**Request:**
```json
{
  "company": "openai",
  "query": "What are OpenAI's key innovations?",
  "mode": "technical",
  "model": "gpt-4o"
}
```

**Response:**
```json
{
  "status": "success",
  "response": "...",
  "insights": [...],
  "entities": [...],
  "citations": [...],
  "metadata": {...}
}
```

### GET /api/files/{company}
List ingested files for a company.

**Response:**
```json
{
  "files": [
    {
      "name": "source.jsonl",
      "size": 1024000,
      "modified": "2024-01-15T10:30:00",
      "doc_count": 150
    }
  ]
}
```

## Color Palette

```css
--cream: #FFFEF9        /* Background */
--white: #FFFFFF        /* Cards/panels */
--crimson: #DC143C      /* Highlights/CTAs */
--dark-gray: #2D2D2D    /* Text */
--light-gray: #E5E5E5   /* Borders */
```

## Typography

- **Headers:** Courier Prime (bold, 700)
- **Body:** IBM Plex Mono (regular, 400)
- **Console:** Courier Prime (monospace)
- **Sizes:** 11px-32px with retro letterSpacing

## Layout

**3-Column Grid:**
- Left (320px): Configuration panel + file browser
- Center (flex): Pipeline console + brief display
- Right (380px): Chat interface

**Responsive:** Collapses to single column on smaller screens

## Future Enhancements

- [ ] Document preview on hover
- [ ] Export brief to PDF/Markdown
- [ ] Citation click → jump to source
- [ ] Dark mode toggle
- [ ] Multi-company comparison view
- [ ] WebSocket support for even faster streaming
- [ ] Animated terminal cursor
- [ ] Sound effects for completion/errors
