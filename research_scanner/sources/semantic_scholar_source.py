"""
Semantic Scholar paper source.
Uses the free Semantic Scholar Academic Graph API.
API docs: https://api.semanticscholar.org/api-docs/
"""

import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Optional

from research_scanner.models import Paper
from .base_source import BaseSource

logger = logging.getLogger(__name__)

S2_API_URL = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = "title,authors,abstract,url,year,externalIds,publicationDate,citationCount,fieldsOfStudy,openAccessPdf"


class SemanticScholarSource(BaseSource):
    """Fetch papers from Semantic Scholar."""

    def __init__(self, api_key: str = "", rate_limit_seconds: float = 1.0, max_retries: int = 3):
        super().__init__(
            name="semantic_scholar",
            rate_limit_seconds=rate_limit_seconds,
            max_retries=max_retries,
        )
        self.api_key = api_key

    def _get_headers(self) -> dict:
        headers = {"User-Agent": "ScholarsTerminal/1.0"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def _parse_paper(self, data: dict) -> Optional[Paper]:
        """Parse a Semantic Scholar paper response into a Paper object."""
        try:
            title = data.get("title", "").strip()
            if not title:
                return None

            authors = [
                a.get("name", "Unknown")
                for a in data.get("authors", [])
                if a.get("name")
            ]

            abstract = data.get("abstract", "") or ""

            pub_date_str = data.get("publicationDate")
            if pub_date_str:
                try:
                    published_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                except ValueError:
                    published_date = datetime(data.get("year", 2025), 1, 1)
            elif data.get("year"):
                published_date = datetime(data["year"], 1, 1)
            else:
                published_date = datetime.now()

            # Build paper ID from external IDs
            ext_ids = data.get("externalIds", {}) or {}
            arxiv_id = ext_ids.get("ArXiv", "")
            doi = ext_ids.get("DOI", "")
            s2_id = data.get("paperId", "")
            paper_id = f"arxiv:{arxiv_id}" if arxiv_id else f"doi:{doi}" if doi else f"s2:{s2_id}"

            url = data.get("url", "")
            if arxiv_id and not url:
                url = f"https://arxiv.org/abs/{arxiv_id}"

            pdf_url = ""
            oap = data.get("openAccessPdf")
            if oap and isinstance(oap, dict):
                pdf_url = oap.get("url", "")

            categories = data.get("fieldsOfStudy") or []
            citation_count = data.get("citationCount", 0) or 0

            return Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                source="semantic_scholar",
                url=url,
                published_date=published_date,
                paper_id=paper_id,
                pdf_url=pdf_url,
                categories=categories,
                citation_count=citation_count,
            )
        except Exception as e:
            logger.warning(f"Failed to parse S2 paper: {e}")
            return None

    def _api_request(self, endpoint: str, params: dict = None) -> dict:
        """Make a request to the Semantic Scholar API."""
        url = f"{S2_API_URL}/{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)

        def _do_request():
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))

        return self._retry_with_backoff(_do_request)

    def fetch_recent(self, days_back: int = 7, max_results: int = 20) -> list[Paper]:
        """Fetch recent AI/ML papers using bulk search."""
        # Semantic Scholar's paper search supports year filtering
        current_year = datetime.now().year
        params = {
            "query": "artificial intelligence machine learning",
            "fields": S2_FIELDS,
            "limit": min(max_results, 100),
            "year": f"{current_year}",
            "fieldsOfStudy": "Computer Science",
        }

        try:
            data = self._api_request("paper/search", params)
            papers = []
            for item in data.get("data", []):
                paper = self._parse_paper(item)
                if paper:
                    papers.append(paper)
            logger.info(f"[semantic_scholar] Fetched {len(papers)} recent papers")
            return papers
        except Exception as e:
            logger.error(f"[semantic_scholar] fetch_recent failed: {e}")
            return []

    def search(self, query: str, max_results: int = 10) -> list[Paper]:
        """Search for papers matching a query."""
        params = {
            "query": query,
            "fields": S2_FIELDS,
            "limit": min(max_results, 100),
            "fieldsOfStudy": "Computer Science",
        }

        try:
            data = self._api_request("paper/search", params)
            papers = []
            for item in data.get("data", []):
                paper = self._parse_paper(item)
                if paper:
                    papers.append(paper)
            logger.info(f"[semantic_scholar] Search '{query}' returned {len(papers)} papers")
            return papers
        except Exception as e:
            logger.error(f"[semantic_scholar] search failed: {e}")
            return []

    def get_paper_details(self, paper_id: str) -> Optional[Paper]:
        """Get full details for a specific paper by S2 ID, arXiv ID, or DOI."""
        try:
            params = {"fields": S2_FIELDS}
            data = self._api_request(f"paper/{paper_id}", params)
            return self._parse_paper(data)
        except Exception as e:
            logger.error(f"[semantic_scholar] get_paper_details failed: {e}")
            return None
