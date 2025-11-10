#!/usr/bin/env python3
"""
FastAPI backend for Interview KB - URL Discovery System
Provides endpoints for discovering relevant URLs for interview preparation
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import sys
sys.path.append(str(Path(__file__).parent.parent))

from ingestion.url_discovery import discover_urls
from bots import FinancialBot, InterviewBot, ScienceBot, NewsBot, SocialBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Interview Knowledge Base - URL Finder",
    description="Advanced URL discovery system for interview preparation",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Request models
class URLDiscoveryRequest(BaseModel):
    """Simple URL discovery (legacy endpoint)"""
    company: str
    person: Optional[str] = None
    max_urls: int = 50


class URLFinderRequest(BaseModel):
    """Advanced URL finder with 5 parallel bots"""
    person_name: str
    company_name: str
    max_results_per_bot: int = 50


# Root endpoint
@app.get("/")
async def root():
    """Serve the main UI."""
    return FileResponse(static_dir / "index.html")


# Simple URL Discovery endpoint (legacy)
@app.post("/api/discover-urls")
async def discover_urls_endpoint(request: URLDiscoveryRequest):
    """
    Simple URL discovery for NotebookLM export.

    This is the legacy endpoint that searches multiple sources
    and returns categorized URLs.
    """
    try:
        logger.info(f"Simple URL discovery: {request.company}" +
                   (f" / {request.person}" if request.person else ""))

        # Run URL discovery in background thread
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

        logger.info(f"Found {len(urls)} URLs across {len(by_category)} categories")

        return {
            "status": "success",
            "total_urls": len(urls),
            "urls": urls,
            "by_category": by_category
        }
    except Exception as e:
        logger.error(f"URL discovery error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Advanced URL Finder endpoint (5 parallel bots)
@app.post("/api/url-finder")
async def url_finder(request: URLFinderRequest):
    """
    Advanced URL discovery using 5 specialized bots running in parallel.

    Bots:
    - Financial Bot: SEC filings, transcripts, investor materials
    - Interview Bot: Videos, podcasts, LinkedIn, blogs
    - Science Bot: PubMed, grants, trials, patents
    - News Bot: Google News, articles, press releases, bios
    - Social Bot: Twitter/X, LinkedIn, professional mentions

    Returns deduplicated URLs ready for NotebookLM import.
    """
    try:
        logger.info(f"URL Finder starting: {request.person_name} at {request.company_name}")

        # Initialize all bots
        bots = [
            FinancialBot(max_results=request.max_results_per_bot),
            InterviewBot(max_results=request.max_results_per_bot),
            ScienceBot(max_results=request.max_results_per_bot),
            NewsBot(max_results=request.max_results_per_bot),
            SocialBot(max_results=request.max_results_per_bot),
        ]

        logger.info(f"Running {len(bots)} bots in parallel...")

        # Run all bots in parallel
        bot_results = await asyncio.gather(*[
            bot.safe_discover(request.person_name, request.company_name)
            for bot in bots
        ])

        # Log bot results
        for result in bot_results:
            bot_name = result.get("name", "unknown")
            status = result.get("status", "unknown")
            count = result.get("count", 0)
            logger.info(f"  {bot_name}: {status} ({count} URLs)")

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

        # Calculate stats
        total_urls = len(all_urls)
        successful_bots = sum(1 for r in bot_results if r["status"] == "success")

        logger.info(f"URL Finder completed: {total_urls} unique URLs from {successful_bots}/{len(bots)} bots")

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
    return {
        "status": "healthy",
        "service": "Interview KB URL Finder",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Interview KB URL Finder service...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
