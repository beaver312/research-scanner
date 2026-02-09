"""
bioRxiv and medRxiv source implementation

These preprint servers use the same API structure.
bioRxiv: Biology preprints
medRxiv: Medical preprints
"""

import requests
from datetime import datetime, timedelta
from typing import List, Optional
import time
import logging

from research_scanner.paper import Paper

logger = logging.getLogger(__name__)


class PrePrintServerBase:
    """
    Base class for bioRxiv/medRxiv preprint servers
    They share the same API structure
    """
    
    def __init__(self, server_name: str, base_url: str):
        self.server_name = server_name
        self.base_url = base_url
        self.source_name = server_name.lower()
        
    def fetch_papers(
        self,
        days_back: int = 7,
        subject_areas: Optional[List[str]] = None,
        cursor: int = 0,
        max_results: int = 100
    ) -> List[Paper]:
        """
        Fetch papers from the preprint server
        
        Args:
            days_back: How many days back to search
            subject_areas: Optional filter by subject areas
            cursor: Pagination cursor (0 for first page)
            max_results: Maximum papers to return
            
        Returns:
            List of Paper objects
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Format dates as YYYY-MM-DD
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        papers = []
        
        try:
            # Construct API URL
            # Format: https://api.biorxiv.org/details/biorxiv/2024-01-01/2024-01-08/0
            url = f"{self.base_url}/details/{self.source_name}/{start_str}/{end_str}/{cursor}"
            
            logger.info(f"Fetching from {self.server_name}: {url}")
            
            # Respect rate limits - be gentle with preprint servers
            time.sleep(1)
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response
            collection = data.get('collection', [])
            
            logger.info(f"{self.server_name}: Found {len(collection)} papers")
            
            for item in collection:
                # Filter by subject areas if specified
                if subject_areas:
                    paper_category = item.get('category', '').lower()
                    if not any(area.lower() in paper_category for area in subject_areas):
                        continue
                
                paper = self._parse_paper(item)
                if paper:
                    papers.append(paper)
                    
                    if len(papers) >= max_results:
                        break
            
            logger.info(f"{self.server_name}: Parsed {len(papers)} relevant papers")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from {self.server_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in {self.server_name} fetch: {e}")
        
        return papers
    
    def _parse_paper(self, item: dict) -> Optional[Paper]:
        """Parse a single paper from API response"""
        try:
            # Extract authors
            authors = []
            for author in item.get('rel_authors', []):
                if isinstance(author, dict):
                    name = author.get('author_name', '').strip()
                    if name:
                        authors.append(name)
                elif isinstance(author, str):
                    authors.append(author.strip())
            
            # Parse date
            date_str = item.get('rel_date', '')
            try:
                published_date = datetime.strptime(date_str, '%Y-%m-%d')
            except:
                published_date = datetime.now()
            
            # Construct paper object
            paper = Paper(
                title=item.get('rel_title', '').strip(),
                authors=authors,
                abstract=item.get('rel_abs', '').strip(),
                published_date=published_date,
                url=item.get('rel_link', ''),
                source=self.source_name,
                doi=item.get('rel_doi', ''),
                categories=[item.get('category', '')] if item.get('category') else []
            )
            
            return paper
            
        except Exception as e:
            logger.error(f"Error parsing {self.server_name} paper: {e}")
            return None


class BioRxivSource(PrePrintServerBase):
    """
    bioRxiv preprint server - biology papers
    
    Subject areas include:
    - Animal Behavior and Cognition
    - Biochemistry
    - Bioengineering
    - Bioinformatics
    - Biophysics
    - Cancer Biology
    - Cell Biology
    - Developmental Biology
    - Ecology
    - Evolutionary Biology
    - Genetics
    - Genomics
    - Immunology
    - Microbiology
    - Molecular Biology
    - Neuroscience
    - Paleontology
    - Pathology
    - Pharmacology and Toxicology
    - Physiology
    - Plant Biology
    - Scientific Communication and Education
    - Synthetic Biology
    - Systems Biology
    - Zoology
    """
    
    def __init__(self):
        super().__init__(
            server_name="bioRxiv",
            base_url="https://api.biorxiv.org"
        )


class MedRxivSource(PrePrintServerBase):
    """
    medRxiv preprint server - medical papers
    
    Subject areas include:
    - Addiction Medicine
    - Allergy and Immunology
    - Anesthesia
    - Cardiovascular Medicine
    - Dentistry and Oral Medicine
    - Dermatology
    - Emergency Medicine
    - Endocrinology
    - Epidemiology
    - Forensic Medicine
    - Gastroenterology
    - Genetic and Genomic Medicine
    - Geriatric Medicine
    - Health Economics
    - Health Informatics
    - Health Policy
    - Health Systems and Quality Improvement
    - Hematology
    - HIV/AIDS
    - Infectious Diseases
    - Intensive Care and Critical Care Medicine
    - Medical Education
    - Medical Ethics
    - Nephrology
    - Neurology
    - Nursing
    - Nutrition
    - Obstetrics and Gynecology
    - Occupational and Environmental Health
    - Oncology
    - Ophthalmology
    - Orthopedics
    - Otolaryngology
    - Pain Medicine
    - Palliative Medicine
    - Pathology
    - Pediatrics
    - Pharmacology and Therapeutics
    - Primary Care Research
    - Psychiatry and Clinical Psychology
    - Public and Global Health
    - Radiology and Imaging
    - Rehabilitation Medicine and Physical Therapy
    - Respiratory Medicine
    - Rheumatology
    - Sexual and Reproductive Health
    - Sports Medicine
    - Surgery
    - Toxicology
    - Transplantation
    - Urology
    """
    
    def __init__(self):
        super().__init__(
            server_name="medRxiv",
            base_url="https://api.medrxiv.org"
        )


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing bioRxiv...")
    biorxiv = BioRxivSource()
    bio_papers = biorxiv.fetch_papers(
        days_back=7,
        subject_areas=["genetics", "molecular biology"],
        max_results=10
    )
    print(f"Found {len(bio_papers)} biology papers")
    if bio_papers:
        print(f"Sample: {bio_papers[0].title}")
    
    print("\nTesting medRxiv...")
    medrxiv = MedRxivSource()
    med_papers = medrxiv.fetch_papers(
        days_back=7,
        subject_areas=["cardiology", "surgery"],
        max_results=10
    )
    print(f"Found {len(med_papers)} medical papers")
    if med_papers:
        print(f"Sample: {med_papers[0].title}")
