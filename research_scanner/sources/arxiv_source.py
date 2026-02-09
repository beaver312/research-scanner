"""
arXiv paper source.
Uses the arXiv REST API directly (no external package dependency).
API docs: https://info.arxiv.org/help/api/basics.html
"""

import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional

from research_scanner.models import Paper
from .base_source import BaseSource

logger = logging.getLogger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


class ArxivSource(BaseSource):
    """Fetch papers from arXiv using their public API."""

    def __init__(self, rate_limit_seconds: float = 3.0, max_retries: int = 3):
        super().__init__(
            name="arxiv",
            rate_limit_seconds=rate_limit_seconds,
            max_retries=max_retries,
        )

    def _parse_entry(self, entry: ET.Element) -> Optional[Paper]:
        """Parse a single Atom entry into a Paper object."""
        try:
            title = entry.find(f"{ATOM_NS}title")
            title_text = title.text.strip().replace("\n", " ") if title is not None and title.text else ""

            summary = entry.find(f"{ATOM_NS}summary")
            abstract = summary.text.strip().replace("\n", " ") if summary is not None and summary.text else ""

            # Authors
            authors = []
            for author_el in entry.findall(f"{ATOM_NS}author"):
                name_el = author_el.find(f"{ATOM_NS}name")
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())

            # Published date
            published_el = entry.find(f"{ATOM_NS}published")
            published_date = datetime.now()
            if published_el is not None and published_el.text:
                published_date = datetime.fromisoformat(published_el.text.replace("Z", "+00:00"))

            # Links - find PDF and abstract URLs
            url = ""
            pdf_url = ""
            for link in entry.findall(f"{ATOM_NS}link"):
                href = link.get("href", "")
                link_type = link.get("type", "")
                link_title = link.get("title", "")
                if link_title == "pdf" or link_type == "application/pdf":
                    pdf_url = href
                elif link.get("rel") == "alternate":
                    url = href

            # arXiv ID from the <id> element
            id_el = entry.find(f"{ATOM_NS}id")
            arxiv_id = ""
            if id_el is not None and id_el.text:
                # Format: http://arxiv.org/abs/2401.12345v1
                arxiv_id = id_el.text.split("/abs/")[-1]

            # Categories
            categories = []
            for cat in entry.findall(f"{ARXIV_NS}primary_category"):
                term = cat.get("term", "")
                if term:
                    categories.append(term)
            for cat in entry.findall(f"{ATOM_NS}category"):
                term = cat.get("term", "")
                if term and term not in categories:
                    categories.append(term)

            if not title_text:
                return None

            return Paper(
                title=title_text,
                authors=authors,
                abstract=abstract,
                source="arxiv",
                url=url or f"https://arxiv.org/abs/{arxiv_id}",
                published_date=published_date,
                paper_id=f"arxiv:{arxiv_id}" if arxiv_id else "",
                pdf_url=pdf_url or f"https://arxiv.org/pdf/{arxiv_id}",
                categories=categories,
            )
        except Exception as e:
            logger.warning(f"Failed to parse arXiv entry: {e}")
            return None

    def _query_api(self, search_query: str, start: int = 0, max_results: int = 20) -> list[Paper]:
        """Execute a single arXiv API query."""
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"

        logger.debug(f"[arxiv] Querying: {url}")

        def _do_request():
            req = urllib.request.Request(url, headers={"User-Agent": "ScholarsTerminal/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()

        xml_data = self._retry_with_backoff(_do_request)
        root = ET.fromstring(xml_data)

        papers = []
        for entry in root.findall(f"{ATOM_NS}entry"):
            paper = self._parse_entry(entry)
            if paper:
                papers.append(paper)

        logger.info(f"[arxiv] Query returned {len(papers)} papers")
        return papers

    def fetch_recent(self, days_back: int = 7, max_results: int = 20) -> list[Paper]:
        """Fetch recent AI papers from arXiv."""
        # arXiv API doesn't support date ranges directly, but sorting by
        # submittedDate descending and fetching enough results works well.
        # Search across main AI categories.
        categories = ["cs.AI", "cs.CL", "cs.LG", "cs.CV", "cs.MA", "cs.IR"]
        cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
        query = f"({cat_query})"

        return self._query_api(query, max_results=max_results)

    def search(self, query: str, max_results: int = 10) -> list[Paper]:
        """Search arXiv for papers matching a query string."""
        # Search in title and abstract
        safe_query = query.replace('"', "").strip()
        search_query = f'all:"{safe_query}"'

        return self._query_api(search_query, max_results=max_results)

    def fetch_by_categories(self, categories: list[str], max_results: int = 20) -> list[Paper]:
        """Fetch recent papers from specific arXiv categories."""
        cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
        return self._query_api(f"({cat_query})", max_results=max_results)

    def fetch_by_topics(self, topics: list, days_back: int = 7, max_results: int = 50) -> list[Paper]:
        """
        Enhanced topic-based fetching for arXiv.
        Uses both arXiv categories and keyword searches.
        """
        seen_ids = set()
        all_papers = []

        # Step 1: Collect all arXiv categories from topics
        all_categories = set()
        for topic in topics:
            if hasattr(topic, 'arxiv_categories') and topic.arxiv_categories:
                all_categories.update(topic.arxiv_categories)

        # Step 2: If categories exist, fetch from those first
        if all_categories:
            try:
                logger.info(f"[arxiv] Fetching from categories: {sorted(all_categories)}")
                cat_papers = self.fetch_by_categories(list(all_categories), max_results=max_results)
                for paper in cat_papers:
                    if paper.paper_id not in seen_ids:
                        seen_ids.add(paper.paper_id)
                        all_papers.append(paper)
            except Exception as e:
                logger.error(f"[arxiv] Error fetching by categories: {e}")

        # Step 3: Also search by keywords for topics without categories
        for topic in topics:
            # Skip if we already have enough papers
            if len(all_papers) >= max_results:
                break

            # Only do keyword search if no categories specified for this topic
            if not (hasattr(topic, 'arxiv_categories') and topic.arxiv_categories):
                for keyword in topic.keywords[:2]:  # Limit to first 2 keywords per topic
                    try:
                        papers = self.search(keyword, max_results=10)
                        for paper in papers:
                            if paper.paper_id not in seen_ids:
                                seen_ids.add(paper.paper_id)
                                all_papers.append(paper)
                    except Exception as e:
                        logger.error(f"[arxiv] Error searching keyword '{keyword}': {e}")

        logger.info(f"[arxiv] Fetched {len(all_papers)} unique papers from {len(topics)} topics")
        return all_papers[:max_results]
