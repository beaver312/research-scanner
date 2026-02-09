"""
FastAPI routes for the Research Scanner.
Mount these into the existing Scholars_api.py using:

    from research_scanner.api_routes import create_research_router
    app.include_router(create_research_router(), prefix="/api/research")
"""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Query, HTTPException
from pydantic import BaseModel

from research_scanner.config import ScannerConfig
from research_scanner.scanner import ResearchScanner

logger = logging.getLogger(__name__)

# Module-level scanner instance (initialized on first use)
_scanner: Optional[ResearchScanner] = None


def get_scanner() -> ResearchScanner:
    """Get or create the scanner singleton."""
    global _scanner
    if _scanner is None:
        _scanner = ResearchScanner(ScannerConfig())
    return _scanner


# ── Response models ──────────────────────────────────────────────────

class ScanResponse(BaseModel):
    message: str
    status: str
    results: Optional[dict] = None

class PaperResponse(BaseModel):
    paper_id: str
    title: str
    authors: str
    source: str
    url: str
    published_date: str
    relevance_score: float = 0.0
    topics: str = ""
    summary_excerpt: str = ""

class StatusResponse(BaseModel):
    sources_enabled: list[str]
    topics: list[str]
    relevance_threshold: float
    indexer: dict
    config: dict


# ── Routes ───────────────────────────────────────────────────────────

def create_research_router() -> APIRouter:
    """Create and return the research scanner API router."""
    router = APIRouter(tags=["research"])

    @router.get("/latest", response_model=list[dict])
    async def get_latest_papers(n: int = Query(default=20, le=100)):
        """Get the most recently indexed research papers."""
        scanner = get_scanner()
        papers = scanner.indexer.get_latest_papers(n=n)
        return papers

    @router.get("/search")
    async def search_papers(
        q: str = Query(..., min_length=1, description="Search query"),
        n: int = Query(default=10, le=50),
    ):
        """Search indexed research papers by query."""
        scanner = get_scanner()
        results = scanner.indexer.search_papers(query=q, n_results=n)
        return {"query": q, "count": len(results), "papers": results}

    @router.get("/topics")
    async def get_topics():
        """List configured research topics."""
        scanner = get_scanner()
        topics = [
            {
                "name": t.name,
                "keywords": t.keywords,
                "weight": t.weight,
                "arxiv_categories": t.arxiv_categories,
            }
            for t in scanner.config.topics
        ]
        return {"topics": topics}

    @router.get("/paper/{paper_id}")
    async def get_paper(paper_id: str):
        """Get full details for a specific indexed paper."""
        scanner = get_scanner()
        if not scanner.indexer.is_ready():
            raise HTTPException(status_code=503, detail="Indexer not ready")

        results = scanner.indexer.search_papers(query=paper_id, n_results=5)
        for r in results:
            if r.get("paper_id") == paper_id:
                return r

        raise HTTPException(status_code=404, detail=f"Paper not found: {paper_id}")

    @router.post("/scan", response_model=ScanResponse)
    async def trigger_scan(background_tasks: BackgroundTasks):
        """Trigger a manual scan (runs in background)."""
        scanner = get_scanner()

        def _run_scan():
            try:
                results = scanner.run_scan()
                logger.info(f"Background scan complete: {results}")
            except Exception as e:
                logger.error(f"Background scan failed: {e}")

        background_tasks.add_task(_run_scan)
        return ScanResponse(
            message="Scan started in background",
            status="running",
        )

    @router.post("/scan/sync", response_model=ScanResponse)
    async def trigger_scan_sync():
        """Trigger a scan and wait for completion (synchronous)."""
        scanner = get_scanner()
        try:
            results = scanner.run_scan()
            return ScanResponse(
                message="Scan complete",
                status="complete",
                results=results,
            )
        except Exception as e:
            logger.error(f"Sync scan failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/status", response_model=StatusResponse)
    async def get_status():
        """Get scanner status and configuration."""
        scanner = get_scanner()
        return scanner.get_status()

    return router
