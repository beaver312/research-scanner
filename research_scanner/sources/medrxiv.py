"""
medRxiv source for medical preprints.

medRxiv is a free online archive for complete but unpublished medical research.
API Documentation: https://api.medrxiv.org/
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Optional
from ..models import Paper

class MedRxivSource:
    """Fetch preprints from medRxiv"""
    
    def __init__(self):
        """Initialize medRxiv source"""
        self.base_url = "https://api.medrxiv.org/details/medrxiv"
        self.rate_limit_delay = 0.5  # 0.5 second between requests
        
    def fetch_papers(
        self,
        queries: Optional[List[str]] = None,
        days_back: int = 7,
        max_results: int = 50
    ) -> List[Paper]:
        """
        Fetch papers from medRxiv
        
        Args:
            queries: Not used for medRxiv (no query support), kept for interface consistency
            days_back: How many days to look back
            max_results: Maximum papers to return
            
        Returns:
            List of Paper objects
        """
        # medRxiv API uses date ranges
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
                paper = self._parse_medrxiv_article(article)
                if paper:
                    papers.append(paper)
            
            return papers
            
        except requests.exceptions.RequestException as e:
            print(f"[medRxiv] Error fetching papers: {e}")
            return []
    
    def _parse_medrxiv_article(self, article: dict) -> Optional[Paper]:
        """Parse medRxiv article JSON into Paper object"""
        
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
            url = f"https://www.medrxiv.org/content/{doi}" if doi else ''
            
            # Category (medRxiv uses subject areas)
            category = article.get('category', 'Medical Research')
            
            return Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                published_date=pub_date,
                url=url,
                source='medrxiv',
                categories=[category],
                doi=doi
            )
            
        except Exception as e:
            print(f"[medRxiv] Error parsing article: {e}")
            return None


# Example usage
if __name__ == '__main__':
    # Create source
    medrxiv = MedRxivSource()
    
    # Fetch recent papers
    print("Fetching recent medical preprints from medRxiv...")
    papers = medrxiv.fetch_papers(days_back=7, max_results=20)
    
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
    print("Filtering for 'cardiac' papers...")
    cardiac_papers = medrxiv.fetch_papers(
        queries=["cardiac", "heart"],
        days_back=14,
        max_results=10
    )
    
    print(f"\nFound {len(cardiac_papers)} cardiac-related papers:")
    for i, paper in enumerate(cardiac_papers, 1):
        print(f"{i}. {paper.title[:70]}...")
