"""
Research Paper Review System
Staging workflow for manual approval before adding to permanent database
"""

import chromadb
from chromadb.config import Settings
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path

CHROMA_DB_PATH = r"D:\Claude\Projects\scholars-terminal\data\vector_db"

class PaperReviewer:
    """Manages staged papers awaiting review"""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Staging collection for papers under review
        self.staging = self._get_or_create_collection("research_papers_staging")
        
        # Permanent collection for approved papers
        self.permanent = self._get_or_create_collection("research_papers")
        
        # Rejected papers log
        self.rejected_log = Path(CHROMA_DB_PATH).parent / "rejected_papers.json"
        
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.client.get_collection(name=name)
        except:
            return self.client.create_collection(
                name=name,
                metadata={"description": f"{name} collection"}
            )
    
    def get_staged_papers(
        self, 
        sort_by: str = "relevance",
        limit: int = 20,
        topic_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Get papers from staging area with sorting
        
        sort_by options:
        - 'relevance': Highest relevance first
        - 'date': Newest first
        - 'citations': Most cited first
        - 'topic': Group by topic
        """
        # Get all staged papers
        results = self.staging.get(
            include=["metadatas", "documents"]
        )
        
        if not results['ids']:
            return []
        
        # Build paper list
        papers = []
        for i, paper_id in enumerate(results['ids']):
            metadata = results['metadatas'][i]
            
            # Apply topic filter if specified
            if topic_filter and topic_filter not in metadata.get('topics', ''):
                continue
            
            papers.append({
                'id': paper_id,
                'title': metadata.get('title', 'Untitled'),
                'authors': metadata.get('authors', 'Unknown'),
                'source': metadata.get('source', 'unknown'),
                'published_date': metadata.get('published_date', ''),
                'topics': metadata.get('topics', ''),
                'relevance_score': float(metadata.get('relevance_score', 0)),
                'citation_count': int(metadata.get('citation_count', 0)),
                'summary': metadata.get('summary_excerpt', ''),
                'url': metadata.get('url', ''),
                'staged_at': metadata.get('indexed_at', '')
            })
        
        # Sort papers
        if sort_by == 'relevance':
            papers.sort(key=lambda x: x['relevance_score'], reverse=True)
        elif sort_by == 'date':
            papers.sort(key=lambda x: x['published_date'], reverse=True)
        elif sort_by == 'citations':
            papers.sort(key=lambda x: x['citation_count'], reverse=True)
        elif sort_by == 'topic':
            papers.sort(key=lambda x: x['topics'])
        
        return papers[:limit]
    
    def preview_paper(self, paper_id: str) -> Optional[Dict]:
        """Get detailed view of a single paper"""
        result = self.staging.get(
            ids=[paper_id],
            include=["metadatas", "documents"]
        )
        
        if not result['ids']:
            return None
        
        metadata = result['metadatas'][0]
        content = result['documents'][0]
        
        return {
            'id': paper_id,
            'title': metadata.get('title', 'Untitled'),
            'authors': metadata.get('authors', 'Unknown'),
            'source': metadata.get('source', 'unknown'),
            'published_date': metadata.get('published_date', ''),
            'topics': metadata.get('topics', ''),
            'relevance_score': float(metadata.get('relevance_score', 0)),
            'citation_count': int(metadata.get('citation_count', 0)),
            'summary': metadata.get('summary_excerpt', ''),
            'full_content': content,
            'url': metadata.get('url', ''),
            'pdf_url': metadata.get('pdf_url', ''),
            'categories': metadata.get('categories', ''),
            'staged_at': metadata.get('indexed_at', '')
        }
    
    def approve_paper(self, paper_id: str) -> bool:
        """Move paper from staging to permanent collection"""
        # Get paper from staging
        result = self.staging.get(
            ids=[paper_id],
            include=["metadatas", "documents", "embeddings"]
        )
        
        if not result['ids']:
            print(f"Paper {paper_id} not found in staging")
            return False
        
        # Add to permanent collection
        self.permanent.add(
            ids=[paper_id],
            metadatas=[result['metadatas'][0]],
            documents=[result['documents'][0]],
            embeddings=[result['embeddings'][0]] if result['embeddings'] else None
        )
        
        # Remove from staging
        self.staging.delete(ids=[paper_id])
        
        print(f"✓ Approved: {result['metadatas'][0].get('title', paper_id)}")
        return True
    
    def reject_paper(self, paper_id: str, reason: str = "") -> bool:
        """Remove paper from staging and log rejection"""
        # Get paper details
        result = self.staging.get(
            ids=[paper_id],
            include=["metadatas"]
        )
        
        if not result['ids']:
            print(f"Paper {paper_id} not found in staging")
            return False
        
        # Log rejection
        rejection = {
            'paper_id': paper_id,
            'title': result['metadatas'][0].get('title', 'Unknown'),
            'rejected_at': datetime.now().isoformat(),
            'reason': reason
        }
        
        # Load existing rejections
        rejections = []
        if self.rejected_log.exists():
            with open(self.rejected_log, 'r') as f:
                rejections = json.load(f)
        
        rejections.append(rejection)
        
        # Save updated rejections
        with open(self.rejected_log, 'w') as f:
            json.dump(rejections, f, indent=2)
        
        # Remove from staging
        self.staging.delete(ids=[paper_id])
        
        print(f"✗ Rejected: {result['metadatas'][0].get('title', paper_id)}")
        if reason:
            print(f"  Reason: {reason}")
        return True
    
    def approve_batch(self, paper_ids: List[str]) -> Dict[str, int]:
        """Approve multiple papers at once"""
        approved = 0
        failed = 0
        
        for paper_id in paper_ids:
            if self.approve_paper(paper_id):
                approved += 1
            else:
                failed += 1
        
        return {'approved': approved, 'failed': failed}
    
    def reject_batch(self, paper_ids: List[str], reason: str = "") -> Dict[str, int]:
        """Reject multiple papers at once"""
        rejected = 0
        failed = 0
        
        for paper_id in paper_ids:
            if self.reject_paper(paper_id, reason):
                rejected += 1
            else:
                failed += 1
        
        return {'rejected': rejected, 'failed': failed}
    
    def get_stats(self) -> Dict:
        """Get statistics about staged vs approved papers"""
        staged_count = self.staging.count()
        approved_count = self.permanent.count()
        
        # Load rejection stats
        rejected_count = 0
        if self.rejected_log.exists():
            with open(self.rejected_log, 'r') as f:
                rejected_count = len(json.load(f))
        
        return {
            'staged': staged_count,
            'approved': approved_count,
            'rejected': rejected_count,
            'total_processed': approved_count + rejected_count
        }
    
    def auto_approve_by_criteria(
        self,
        min_relevance: float = 0.8,
        min_citations: int = 100,
        max_papers: int = 10
    ) -> List[str]:
        """
        Automatically approve high-quality papers
        
        Criteria:
        - High relevance score (≥0.8)
        - Well-cited (≥100 citations)
        - Recent and relevant
        """
        papers = self.get_staged_papers(sort_by='relevance', limit=100)
        approved = []
        
        for paper in papers:
            if len(approved) >= max_papers:
                break
            
            if (paper['relevance_score'] >= min_relevance and 
                paper['citation_count'] >= min_citations):
                
                if self.approve_paper(paper['id']):
                    approved.append(paper['id'])
        
        return approved


if __name__ == "__main__":
    reviewer = PaperReviewer()
    stats = reviewer.get_stats()
    
    print("\n" + "=" * 60)
    print("  RESEARCH PAPER REVIEW SYSTEM")
    print("=" * 60)
    print(f"Staged (awaiting review): {stats['staged']}")
    print(f"Approved (in database):   {stats['approved']}")
    print(f"Rejected (declined):      {stats['rejected']}")
    print(f"Total processed:          {stats['total_processed']}")
    print("=" * 60 + "\n")
