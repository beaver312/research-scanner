"""
IEEE Xplore source for engineering and technology papers.

API Documentation: https://developer.ieee.org/
Note: Requires IEEE API key (free tier available)
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Optional
from ..models import Paper

class IEEESource:
    """Fetch papers from IEEE Xplore database"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize IEEE source
        
        Args:
            api_key: IEEE API key (get from https://developer.ieee.org/)
                    If None, will try to load from environment IEEEXPLORE_API_KEY
        """
        import os
        self.api_key = api_key or os.getenv('IEEEXPLORE_API_KEY')
        self.base_url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
        self.rate_limit_delay = 1.0  # 1 second between requests
        
    def fetch_papers(
        self,
        queries: List[str],
        days_back: int = 7,
        max_results: int = 50
    ) -> List[Paper]:
        """
        Fetch papers from IEEE Xplore
        
        Args:
            queries: List of search queries
            days_back: How many days to look back
            max_results: Maximum papers to return
            
        Returns:
            List of Paper objects
        """
        if not self.api_key:
            print("[IEEE] Warning: No API key found. Set IEEEXPLORE_API_KEY environment variable.")
            print("[IEEE] Get free key at: https://developer.ieee.org/")
            return []
        
        all_papers = []
        
        for query in queries:
            papers = self._query_ieee(query, days_back, max_results)
            all_papers.extend(papers)
            time.sleep(self.rate_limit_delay)
        
        # Deduplicate by DOI
        seen_dois = set()
        unique_papers = []
        for paper in all_papers:
            if paper.url not in seen_dois:
                seen_dois.add(paper.url)
                unique_papers.append(paper)
        
        return unique_papers[:max_results]
    
    def _query_ieee(self, query: str, days_back: int, max_results: int) -> List[Paper]:
        """Execute a single IEEE query"""
        
        # Build date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # IEEE API parameters
        params = {
            'apikey': self.api_key,
            'querytext': query,
            'max_records': min(max_results, 200),  # IEEE limit
            'start_record': 1,
            'sort_field': 'publication_date',
            'sort_order': 'desc',
            'start_year': start_date.year,
            'end_year': end_date.year
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            articles = data.get('articles', [])
            
            for article in articles:
                paper = self._parse_ieee_article(article)
                if paper:
                    papers.append(paper)
            
            return papers
            
        except requests.exceptions.RequestException as e:
            print(f"[IEEE] Error querying '{query}': {e}")
            return []
    
    def _parse_ieee_article(self, article: dict) -> Optional[Paper]:
        """Parse IEEE article JSON into Paper object"""
        
        try:
            # Extract metadata
            title = article.get('title', 'Untitled')
            abstract = article.get('abstract', '')
            authors = [
                author.get('full_name', '')
                for author in article.get('authors', {}).get('authors', [])
            ]
            
            # Publication date
            pub_year = article.get('publication_year')
            pub_date = datetime(int(pub_year), 1, 1) if pub_year else datetime.now()
            
            # DOI and URL
            doi = article.get('doi', '')
            url = f"https://doi.org/{doi}" if doi else article.get('html_url', '')
            
            # Categories/keywords
            categories = []
            if 'index_terms' in article:
                terms = article['index_terms']
                if 'ieee_terms' in terms:
                    categories.extend(terms['ieee_terms'].get('terms', []))
                if 'author_terms' in terms:
                    categories.extend(terms['author_terms'].get('terms', []))
            
            return Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                published_date=pub_date,
                url=url,
                source='ieee',
                categories=categories[:10],  # Limit categories
                doi=doi
            )
            
        except Exception as e:
            print(f"[IEEE] Error parsing article: {e}")
            return None


# Example usage
if __name__ == '__main__':
    import os
    
    # Set your API key
    api_key = os.getenv('IEEEXPLORE_API_KEY')
    if not api_key:
        print("Please set IEEEXPLORE_API_KEY environment variable")
        print("Get free key at: https://developer.ieee.org/")
        exit(1)
    
    # Create source
    ieee = IEEESource(api_key)
    
    # Test queries for aerospace engineering
    queries = [
        "aerospace propulsion systems",
        "aircraft aerodynamics",
        "spacecraft design"
    ]
    
    # Fetch papers
    papers = ieee.fetch_papers(queries, days_back=30, max_results=10)
    
    print(f"\nFound {len(papers)} papers from IEEE Xplore:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        if len(paper.authors) > 3:
            print(f"   ... and {len(paper.authors) - 3} more")
        print(f"   Published: {paper.published_date.strftime('%Y-%m-%d')}")
        print(f"   DOI: {paper.doi}")
        if paper.categories:
            print(f"   Categories: {', '.join(paper.categories[:5])}")
