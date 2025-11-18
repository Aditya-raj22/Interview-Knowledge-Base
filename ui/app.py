#!/usr/bin/env python3
"""
FastAPI backend for Interview KB URL Discovery
Provides endpoint for URL discovery only
"""
import asyncio
import json
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Interview Knowledge Base - URL Discovery")

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
class URLDiscoveryRequest(BaseModel):
    company: str
    person: Optional[str] = None
    max_urls: int = 50


# Root endpoint
@app.get("/")
async def root():
    """Serve the main UI."""
    return FileResponse(Path(__file__).parent / "static" / "index.html")


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


# Health check
@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
