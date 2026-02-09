"""
bioRxiv source for biology preprints.

bioRxiv is a free online archive for biology research preprints.
API Documentation: https://api.biorxiv.org/
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Optional
from ..models import Paper

class BioRxivSource:
    """Fetch preprints from bioRxiv"""
    
    def __init__(self):
        """Initialize bioRxiv source"""
        self.base_url = "https://api.biorxiv.org/details/biorxiv"
        self.rate_limit_delay = 0.5  # 0.5 second between requests
        
    def fetch_papers(
        self,
        queries: Optional[List[str]] = None,
        days_back: int = 7,
        max_results: int = 50
    ) -> List[Paper]:
        """
        Fetch papers from bioRxiv
        
        Args:
            queries: Keywords to filter by (optional)
            days_back: How many days to look back
            max_results: Maximum papers to return
            
        Returns:
            List of Paper objects
        """
        # bioRxiv API uses date ranges
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        papers = self._fetch_by_date_range(start_date, end_date)
        
        # If queries provided, filter by keywords in title/abstract
        if queries and papers:
            filtered = []
            for paper in papers:
                text = (paper.title + " " + paper.abstract).lower()
                if any(q.lower() in text for q in queries):
                    filtered.append(paper)
            papers = filtered
        
        return papers[:max_results]
    
    def _fetch_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Paper]:
        """Fetch papers within date range"""
        
        # Format dates for API (YYYY-MM-DD)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/{start_str}/{end_str}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            articles = data.get('collection', [])
            
            for article in articles:
                paper = self._parse_biorxiv_article(article)
                if paper:
                    papers.append(paper)
            
            return papers
            
        except requests.exceptions.RequestException as e:
            print(f"[bioRxiv] Error fetching papers: {e}")
            return []
    
    def _parse_biorxiv_article(self, article: dict) -> Optional[Paper]:
        """Parse bioRxiv article JSON into Paper object"""
        
        try:
            # Extract metadata
            title = article.get('title', 'Untitled')
            abstract = article.get('abstract', '')
            
            # Authors - parse from string
            authors_str = article.get('authors', '')
            authors = [a.strip() for a in authors_str.split(';')] if authors_str else []
            
            # Publication date
            date_str = article.get('date', '')
            if date_str:
                try:
                    pub_date = datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    pub_date = datetime.now()
            else:
                pub_date = datetime.now()
            
            # DOI and URL
            doi = article.get('doi', '')
            url = f"https://www.biorxiv.org/content/{doi}" if doi else ''
            
            # Category (bioRxiv uses subject areas)
            category = article.get('category', 'Biology')
            
            return Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                published_date=pub_date,
                url=url,
                source='biorxiv',
                categories=[category],
                doi=doi
            )
            
        except Exception as e:
            print(f"[bioRxiv] Error parsing article: {e}")
            return None


# Example usage
if __name__ == '__main__':
    # Create source
    biorxiv = BioRxivSource()
    
    # Fetch recent papers
    print("Fetching recent biology preprints from bioRxiv...")
    papers = biorxiv.fetch_papers(days_back=7, max_results=20)
    
    print(f"\nFound {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        if len(paper.authors) > 3:
            print(f"   ... and {len(paper.authors) - 3} more")
        print(f"   Published: {paper.published_date.strftime('%Y-%m-%d')}")
        print(f"   Category: {paper.categories[0] if paper.categories else 'N/A'}")
        print(f"   URL: {paper.url}")
    
    # Test with keyword filtering
    print("\n" + "="*70)
    print("Filtering for 'CRISPR' papers...")
    crispr_papers = biorxiv.fetch_papers(
        queries=["CRISPR", "gene editing"],
        days_back=14,
        max_results=10
    )
    
    print(f"\nFound {len(crispr_papers)} CRISPR-related papers:")
    for i, paper in enumerate(crispr_papers, 1):
        print(f"{i}. {paper.title[:70]}...")
