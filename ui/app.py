#!/usr/bin/env python3
"""
FastAPI backend for Interview KB UI
Provides endpoints for pipeline execution, chat, and file browsing
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

import sys
sys.path.append(str(Path(__file__).parent.parent))

import ingestion
import indexing
import generation
from ingestion.url_discovery import discover_urls
from config import DATA_DIR, INDEX_DIR, BRIEF_MODES
from bots import FinancialBot, InterviewBot, ScienceBot, NewsBot, SocialBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Interview Knowledge Base")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


# Request models
class PipelineRequest(BaseModel):
    company: str
    person: Optional[str] = None
    mode: str = "summary"
    model: str = "gpt-4o"
    skip_ingestion: bool = False
    skip_indexing: bool = False


class ChatRequest(BaseModel):
    company: str
    person: Optional[str] = None
    query: str
    mode: str = "summary"
    model: str = "gpt-4o"


class URLDiscoveryRequest(BaseModel):
    company: str
    person: Optional[str] = None
    max_urls: int = 50


class URLFinderRequest(BaseModel):
    person_name: str
    company_name: str
    max_results_per_bot: int = 50


# Root endpoint
@app.get("/")
async def root():
    """Serve the main UI."""
    return FileResponse(Path(__file__).parent / "static" / "index.html")


# SSE endpoint for streaming pipeline progress
@app.post("/api/pipeline/stream")
async def stream_pipeline(request: PipelineRequest):
    """Stream pipeline execution progress using Server-Sent Events."""

    async def generate_events() -> AsyncGenerator[str, None]:
        company_folder = request.company.replace(" ", "_").lower()

        try:
            # Step 1: Ingestion
            if not request.skip_ingestion:
                yield f"data: {json.dumps({'step': 'ingestion', 'status': 'started', 'message': 'Fetching data from sources...'})}\n\n"

                # Run ingestion (blocking, but we'll make it async-friendly)
                output_file = await asyncio.to_thread(
                    ingestion.run_ingestion,
                    request.company,
                    request.person or request.company
                )

                yield f"data: {json.dumps({'step': 'ingestion', 'status': 'completed', 'message': f'Data saved to {output_file.name}'})}\n\n"
            else:
                yield f"data: {json.dumps({'step': 'ingestion', 'status': 'skipped', 'message': 'Using existing data'})}\n\n"

            # Step 2: Indexing
            if not request.skip_indexing:
                yield f"data: {json.dumps({'step': 'indexing', 'status': 'started', 'message': 'Generating embeddings and clustering...'})}\n\n"

                index_dir = await asyncio.to_thread(indexing.build_index, company_folder)

                yield f"data: {json.dumps({'step': 'indexing', 'status': 'completed', 'message': f'Index built at {index_dir.name}/'})}\n\n"
            else:
                yield f"data: {json.dumps({'step': 'indexing', 'status': 'skipped', 'message': 'Using existing index'})}\n\n"

            # Step 3: Generation
            yield f"data: {json.dumps({'step': 'generation', 'status': 'started', 'message': 'Generating interview brief...'})}\n\n"

            brief = await asyncio.to_thread(
                generation.generate_brief,
                company=company_folder,
                person=request.person,
                mode=request.mode,
                model=request.model
            )

            yield f"data: {json.dumps({'step': 'generation', 'status': 'completed', 'message': 'Brief generated successfully', 'brief': brief})}\n\n"

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            yield f"data: {json.dumps({'step': 'error', 'status': 'failed', 'message': str(e)})}\n\n"

    return StreamingResponse(generate_events(), media_type="text/event-stream")


# Chat endpoint for RAG queries
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Run a RAG query and return the response."""
    try:
        company_folder = request.company.replace(" ", "_").lower()

        # Generate brief using the query as context
        brief = await asyncio.to_thread(
            generation.generate_brief,
            company=company_folder,
            person=request.person,
            mode=request.mode,
            model=request.model,
            custom_query=request.query
        )

        return {
            "status": "success",
            "response": brief["summary"],
            "insights": brief["insights"],
            "entities": brief["key_entities"][:5],
            "citations": brief["citations"][:10],
            "metadata": brief["metadata"]
        }
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# File browsing endpoints
@app.get("/api/files/{company}")
async def list_files(company: str):
    """List all ingested files for a company."""
    try:
        company_folder = company.replace(" ", "_").lower()
        raw_dir = Path(DATA_DIR) / company_folder

        if not raw_dir.exists():
            return {"files": [], "message": "No data found for this company"}

        files = []
        for file in raw_dir.glob("*.jsonl"):
            # Read file and count documents
            with open(file, "r") as f:
                docs = [json.loads(line) for line in f]

            files.append({
                "name": file.name,
                "size": file.stat().st_size,
                "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                "doc_count": len(docs)
            })

        return {"files": files}
    except Exception as e:
        logger.error(f"File listing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/{company}/preview")
async def preview_file(company: str, limit: int = 5):
    """Preview first few documents from a company's data."""
    try:
        company_folder = company.replace(" ", "_").lower()
        source_file = Path(DATA_DIR) / company_folder / "source.jsonl"

        if not source_file.exists():
            raise HTTPException(status_code=404, detail="No data found")

        docs = []
        with open(source_file, "r") as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                doc = json.loads(line)
                # Truncate text for preview
                doc["text"] = doc["text"][:500] + "..." if len(doc["text"]) > 500 else doc["text"]
                docs.append(doc)

        return {"documents": docs}
    except Exception as e:
        logger.error(f"Preview error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# URL Discovery endpoint
@app.post("/api/discover-urls")
async def discover_urls_endpoint(request: URLDiscoveryRequest):
    """Discover URLs for NotebookLM export."""
    try:
        logger.info(f"URL discovery for {request.company}" + (f" / {request.person}" if request.person else ""))

        # Run URL discovery
        urls = await asyncio.to_thread(
            discover_urls,
            company=request.company,
            person=request.person,
            max_urls=request.max_urls
        )

        # Group by category
        by_category = {}
        for url_data in urls:
            category = url_data["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(url_data)

        return {
            "status": "success",
            "total_urls": len(urls),
            "urls": urls,
            "by_category": by_category
        }
    except Exception as e:
        logger.error(f"URL discovery error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# URL Finder endpoint (with parallel bots)
@app.post("/api/url-finder")
async def url_finder(request: URLFinderRequest):
    """
    Advanced URL discovery using 5 specialized bots running in parallel.

    Returns consolidated results from:
    - Financial Bot: SEC filings, transcripts, investor materials
    - Interview Bot: Videos, podcasts, LinkedIn, blogs
    - Science Bot: PubMed, grants, trials, patents
    - News Bot: Google News, articles, press releases, bios
    - Social Bot: Twitter/X, LinkedIn, professional mentions
    """
    try:
        logger.info(f"URL Finder for {request.person_name} at {request.company_name}")

        # Initialize all bots
        bots = [
            FinancialBot(max_results=request.max_results_per_bot),
            InterviewBot(max_results=request.max_results_per_bot),
            ScienceBot(max_results=request.max_results_per_bot),
            NewsBot(max_results=request.max_results_per_bot),
            SocialBot(max_results=request.max_results_per_bot),
        ]

        # Run all bots in parallel
        bot_results = await asyncio.gather(*[
            bot.safe_discover(request.person_name, request.company_name)
            for bot in bots
        ])

        # Deduplicate URLs across all bots
        all_urls = []
        seen_normalized = set()

        for bot_result in bot_results:
            for url_dict in bot_result.get("results", []):
                # Reconstruct URLResult to use normalization
                from bots.base import URLResult
                url_result = URLResult(**url_dict)
                normalized = url_result.normalized_url()

                if normalized not in seen_normalized:
                    seen_normalized.add(normalized)
                    all_urls.append(url_dict)

        # Calculate total counts
        total_urls = len(all_urls)
        successful_bots = sum(1 for r in bot_results if r["status"] == "success")

        return {
            "status": "success",
            "person_name": request.person_name,
            "company_name": request.company_name,
            "total_urls": total_urls,
            "bots": bot_results,
            "all_urls": all_urls,
            "metadata": {
                "successful_bots": successful_bots,
                "failed_bots": len(bots) - successful_bots,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"URL Finder error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Health check
@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
