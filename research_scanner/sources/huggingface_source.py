"""
HuggingFace Daily Papers source.
Fetches curated AI papers from the HuggingFace papers page.
Uses the HuggingFace API endpoint for papers.
"""

import json
import logging
import urllib.request
from datetime import datetime, timedelta
from typing import Optional

from research_scanner.models import Paper
from .base_source import BaseSource

logger = logging.getLogger(__name__)

HF_PAPERS_API = "https://huggingface.co/api/daily_papers"


class HuggingFaceSource(BaseSource):
    """Fetch curated daily papers from HuggingFace."""

    def __init__(self, rate_limit_seconds: float = 1.0, max_retries: int = 3):
        super().__init__(
            name="huggingface",
            rate_limit_seconds=rate_limit_seconds,
            max_retries=max_retries,
        )

    def _parse_hf_paper(self, data: dict) -> Optional[Paper]:
        """Parse a HuggingFace paper entry into a Paper object."""
        try:
            paper_data = data.get("paper", data)

            title = paper_data.get("title", "").strip()
            if not title:
                return None

            # Authors can be in different formats
            authors_raw = paper_data.get("authors", [])
            authors = []
            for a in authors_raw:
                if isinstance(a, str):
                    authors.append(a)
                elif isinstance(a, dict):
                    name = a.get("name", a.get("user", {}).get("fullname", ""))
                    if name:
                        authors.append(name)

            abstract = paper_data.get("summary", paper_data.get("abstract", "")) or ""

            # Date handling
            pub_date = data.get("publishedAt", paper_data.get("publishedAt", ""))
            if pub_date:
                try:
                    # Handle various date formats
                    if "T" in pub_date:
                        published_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                    else:
                        published_date = datetime.strptime(pub_date, "%Y-%m-%d")
                except ValueError:
                    published_date = datetime.now()
            else:
                published_date = datetime.now()

            # Paper ID - use arXiv ID if available
            arxiv_id = paper_data.get("id", paper_data.get("arxivId", ""))
            paper_id = f"arxiv:{arxiv_id}" if arxiv_id else ""

            url = f"https://huggingface.co/papers/{arxiv_id}" if arxiv_id else ""
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else ""

            upvotes = data.get("paper", {}).get("upvotes", 0)

            return Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                source="huggingface",
                url=url,
                published_date=published_date,
                paper_id=paper_id,
                pdf_url=pdf_url,
                categories=["HuggingFace Daily"],
                citation_count=upvotes,  # Use upvotes as a proxy for popularity
            )
        except Exception as e:
            logger.warning(f"Failed to parse HF paper: {e}")
            return None

    def fetch_recent(self, days_back: int = 7, max_results: int = 30) -> list[Paper]:
        """Fetch recent daily papers from HuggingFace."""

        def _do_request():
            req = urllib.request.Request(
                HF_PAPERS_API,
                headers={"User-Agent": "ScholarsTerminal/1.0"},
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))

        try:
            data = self._retry_with_backoff(_do_request)

            if not isinstance(data, list):
                logger.warning(f"[huggingface] Unexpected response format: {type(data)}")
                return []

            cutoff = datetime.now() - timedelta(days=days_back)
            papers = []
            for item in data[:max_results]:
                paper = self._parse_hf_paper(item)
                if paper and paper.published_date.replace(tzinfo=None) >= cutoff:
                    papers.append(paper)

            logger.info(f"[huggingface] Fetched {len(papers)} papers from last {days_back} days")
            return papers

        except Exception as e:
            logger.error(f"[huggingface] fetch_recent failed: {e}")
            return []

    def search(self, query: str, max_results: int = 10) -> list[Paper]:
        """
        Search HuggingFace papers by keyword.
        HF daily papers API doesn't support search directly,
        so we fetch all recent and filter locally.
        """
        all_papers = self.fetch_recent(days_back=30, max_results=100)
        query_lower = query.lower()

        matching = [
            p for p in all_papers
            if query_lower in p.title.lower() or query_lower in p.abstract.lower()
        ]

        logger.info(f"[huggingface] Search '{query}' matched {len(matching)}/{len(all_papers)} papers")
        return matching[:max_results]
