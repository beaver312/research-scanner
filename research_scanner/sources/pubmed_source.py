"""
PubMed paper source.
Uses the NCBI E-utilities API to search biomedical literature.
API docs: https://www.ncbi.nlm.nih.gov/books/NBK25500/
"""

import json
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional

from research_scanner.models import Paper
from .base_source import BaseSource

logger = logging.getLogger(__name__)


class PubMedSource(BaseSource):
    """Fetch papers from PubMed using NCBI E-utilities."""

    BASE_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    BASE_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        # NCBI requests 3 requests/sec without key, 10/sec with key
        rate_limit = 0.1 if api_key else 0.35
        super().__init__(name="pubmed", rate_limit_seconds=rate_limit)
        self.email = email or "scholar@example.com"
        self.api_key = api_key

    def fetch_recent(self, days_back: int = 7, max_results: int = 20) -> list[Paper]:
        """Fetch recently published papers from PubMed."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        date_filter = f"{start_date.strftime('%Y/%m/%d')}:{end_date.strftime('%Y/%m/%d')}[dp]"
        
        # Search for any recent papers
        query = f"{date_filter}"
        return self.search(query, max_results=max_results)

    def search(self, query: str, max_results: int = 20) -> list[Paper]:
        """Search PubMed for papers matching query."""
        self._rate_limit()

        # Step 1: Search for PMIDs
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "pub_date",
            "email": self.email,
        }
        if self.api_key:
            search_params["api_key"] = self.api_key

        search_url = f"{self.BASE_SEARCH_URL}?{urllib.parse.urlencode(search_params)}"
        logger.debug(f"[pubmed] Searching: {search_url}")

        try:
            with urllib.request.urlopen(search_url, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                pmids = data.get("esearchresult", {}).get("idlist", [])

            if not pmids:
                logger.info(f"[pubmed] No results for query: {query}")
                return []

            # Step 2: Fetch article details
            self._rate_limit()
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "email": self.email,
            }
            if self.api_key:
                fetch_params["api_key"] = self.api_key

            fetch_url = f"{self.BASE_FETCH_URL}?{urllib.parse.urlencode(fetch_params)}"

            with urllib.request.urlopen(fetch_url, timeout=30) as response:
                xml_data = response.read().decode("utf-8")

            papers = self._parse_pubmed_xml(xml_data)
            logger.info(f"[pubmed] Found {len(papers)} papers for query: {query}")
            return papers

        except Exception as e:
            logger.error(f"[pubmed] Search failed: {e}")
            return []

    def _parse_pubmed_xml(self, xml_data: str) -> list[Paper]:
        """Parse PubMed XML response into Paper objects."""
        papers = []
        root = ET.fromstring(xml_data)

        for article in root.findall(".//PubmedArticle"):
            try:
                # Extract PMID
                pmid = article.find(".//PMID").text

                # Extract basic info
                article_node = article.find(".//Article")
                title = article_node.find(".//ArticleTitle").text or "No title"

                # Abstract
                abstract_nodes = article_node.findall(".//AbstractText")
                abstract = " ".join([node.text or "" for node in abstract_nodes])

                # Authors
                authors = []
                for author in article_node.findall(".//Author"):
                    last = author.find(".//LastName")
                    first = author.find(".//ForeName")
                    if last is not None and first is not None:
                        authors.append(f"{first.text} {last.text}")

                # Publication date
                pub_date_node = article.find(".//PubDate")
                year = pub_date_node.find(".//Year")
                month = pub_date_node.find(".//Month")
                day = pub_date_node.find(".//Day")

                if year is not None:
                    pub_date_str = year.text
                    if month is not None:
                        pub_date_str = f"{year.text}-{month.text}"
                        if day is not None:
                            pub_date_str = f"{year.text}-{month.text}-{day.text}"
                    
                    # Try multiple date formats (PubMed returns month names like "Dec" or "12")
                    date_formats = [
                        "%Y-%m-%d",      # 2024-12-31
                        "%Y-%b-%d",      # 2024-Dec-31
                        "%Y-%B-%d",      # 2024-December-31
                        "%Y-%m",         # 2024-12
                        "%Y-%b",         # 2024-Dec
                        "%Y-%B",         # 2024-December
                        "%Y"             # 2024
                    ]
                    
                    published_date = None
                    for fmt in date_formats:
                        try:
                            published_date = datetime.strptime(pub_date_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if published_date is None:
                        # If all parsing fails, just use current date
                        published_date = datetime.now()
                else:
                    published_date = datetime.now()

                # Create Paper object
                paper = Paper(
                    paper_id=f"pmid_{pmid}",
                    title=title,
                    authors=authors,
                    abstract=abstract or "No abstract available",
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    source="pubmed",
                    published_date=published_date,
                )
                papers.append(paper)

            except Exception as e:
                logger.warning(f"[pubmed] Failed to parse article: {e}")
                continue

        return papers

    def fetch_by_topics(self, topics, days_back: int = 7, max_results: int = 50) -> list[Paper]:
        """
        Fetch papers matching topic keywords from recent days.
        Enhanced to use template-specific queries if available.
        """
        all_papers = []
        seen_ids = set()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        date_filter = f"{start_date.strftime('%Y/%m/%d')}:{end_date.strftime('%Y/%m/%d')}[dp]"

        # Step 1: Use template-specific queries if available
        # (These come from template.sources['pubmed'].queries)
        template_queries = getattr(self, 'template_queries', None)
        if template_queries:
            logger.info(f"[pubmed] Using {len(template_queries)} template-specific queries")
            for query in template_queries:
                full_query = f"{query} AND {date_filter}"
                papers = self.search(full_query, max_results=max_results // len(template_queries))
                
                for paper in papers:
                    if paper.paper_id not in seen_ids:
                        seen_ids.add(paper.paper_id)
                        all_papers.append(paper)
        
        # Step 2: Also search by topic keywords
        for topic in topics:
            if len(all_papers) >= max_results:
                break
                
            # Combine keywords with OR
            keyword_query = " OR ".join([f'"{kw}"' for kw in topic.keywords[:3]])  # Limit to 3 keywords
            full_query = f"({keyword_query}) AND {date_filter}"

            papers = self.search(full_query, max_results=max_results // len(topics))

            for paper in papers:
                if paper.paper_id not in seen_ids:
                    seen_ids.add(paper.paper_id)
                    all_papers.append(paper)

        logger.info(f"[pubmed] Fetched {len(all_papers)} unique papers from {len(topics)} topics")
        return all_papers[:max_results]
    
    def set_template_queries(self, queries: list[str]):
        """Set template-specific queries to use instead of/in addition to topic keywords."""
        self.template_queries = queries
