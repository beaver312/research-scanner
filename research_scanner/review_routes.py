"""
API Routes for Research Paper Review System
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from .reviewer import PaperReviewer

router = APIRouter()
reviewer = PaperReviewer()


class ApproveRequest(BaseModel):
    paper_ids: List[str]


class RejectRequest(BaseModel):
    paper_ids: List[str]
    reason: Optional[str] = ""


@router.get("/staged")
async def get_staged_papers(
    sort_by: str = Query("relevance", regex="^(relevance|date|citations|topic)$"),
    limit: int = Query(20, ge=1, le=100),
    topic: Optional[str] = None
):
    """
    Get papers in staging area awaiting review
    
    Sort options:
    - relevance: Highest relevance first (default)
    - date: Newest first
    - citations: Most cited first
    - topic: Grouped by topic
    """
    papers = reviewer.get_staged_papers(
        sort_by=sort_by,
        limit=limit,
        topic_filter=topic
    )
    
    return {
        "count": len(papers),
        "sort_by": sort_by,
        "papers": papers
    }


@router.get("/staged/{paper_id}")
async def preview_paper(paper_id: str):
    """Get detailed preview of a staged paper"""
    paper = reviewer.preview_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found in staging")
    
    return paper


@router.post("/approve")
async def approve_papers(request: ApproveRequest):
    """Approve paper(s) and move to permanent database"""
    result = reviewer.approve_batch(request.paper_ids)
    
    return {
        "message": f"Processed {len(request.paper_ids)} papers",
        "approved": result['approved'],
        "failed": result['failed']
    }


@router.post("/reject")
async def reject_papers(request: RejectRequest):
    """Reject paper(s) and remove from staging"""
    result = reviewer.reject_batch(request.paper_ids, request.reason)
    
    return {
        "message": f"Processed {len(request.paper_ids)} papers",
        "rejected": result['rejected'],
        "failed": result['failed']
    }


@router.post("/auto-approve")
async def auto_approve(
    min_relevance: float = Query(0.8, ge=0.0, le=1.0),
    min_citations: int = Query(100, ge=0),
    max_papers: int = Query(10, ge=1, le=50)
):
    """
    Automatically approve high-quality papers
    
    Criteria:
    - min_relevance: Minimum relevance score (default 0.8)
    - min_citations: Minimum citation count (default 100)
    - max_papers: Maximum papers to approve (default 10)
    """
    approved = reviewer.auto_approve_by_criteria(
        min_relevance=min_relevance,
        min_citations=min_citations,
        max_papers=max_papers
    )
    
    return {
        "message": f"Auto-approved {len(approved)} papers",
        "approved_count": len(approved),
        "paper_ids": approved
    }


@router.get("/stats")
async def get_review_stats():
    """Get statistics about review process"""
    return reviewer.get_stats()


def create_review_router():
    """Create and return the review router"""
    return router
