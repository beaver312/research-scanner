"""
Template Manager for Domain-Specific Research Configuration
Allows users to select from pre-built research domains or create custom ones
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SourceConfig:
    """Configuration for a research paper source"""
    enabled: bool
    queries: List[str] = None
    categories: List[str] = None
    mesh_terms: List[str] = None
    subjects: List[str] = None


@dataclass
class TopicConfig:
    """Configuration for a research topic"""
    name: str
    keywords: List[str]
    weight: float = 1.0
    arxiv_categories: List[str] = None


@dataclass
class DomainTemplate:
    """Complete domain research template"""
    domain: str
    description: str
    sources: Dict[str, SourceConfig]
    topics: List[TopicConfig]
    relevance_threshold: float = 0.3
    days_lookback: int = 7
    max_papers_per_scan: int = 50


class TemplateManager:
    """Manages research domain templates"""
    
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            # Default to templates directory next to this file
            templates_dir = Path(__file__).parent / "templates"
        
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
    
    def list_templates(self) -> List[Dict[str, str]]:
        """
        List all available domain templates
        
        Returns:
            List of dicts with 'name', 'domain', and 'description'
        """
        templates = []
        
        for template_file in sorted(self.templates_dir.glob("*.yaml")):
            try:
                with open(template_file) as f:
                    data = yaml.safe_load(f)
                    templates.append({
                        'name': template_file.stem,
                        'domain': data.get('domain', 'Unknown'),
                        'description': data.get('description', '')
                    })
            except Exception as e:
                print(f"Warning: Could not load template {template_file.name}: {e}")
        
        return templates
    
    def load_template(self, name: str) -> Optional[DomainTemplate]:
        """
        Load a specific template by name
        
        Args:
            name: Template filename without .yaml extension
            
        Returns:
            DomainTemplate object or None if not found
        """
        template_path = self.templates_dir / f"{name}.yaml"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template '{name}' not found at {template_path}")
        
        with open(template_path) as f:
            data = yaml.safe_load(f)
        
        # Parse sources
        sources = {}
        for source_name, source_data in data.get('sources', {}).items():
            sources[source_name] = SourceConfig(
                enabled=source_data.get('enabled', False),
                queries=source_data.get('queries'),
                categories=source_data.get('categories'),
                mesh_terms=source_data.get('mesh_terms'),
                subjects=source_data.get('subjects')
            )
        
        # Parse topics
        topics = []
        for topic_data in data.get('topics', []):
            topics.append(TopicConfig(
                name=topic_data['name'],
                keywords=topic_data['keywords'],
                weight=topic_data.get('weight', 1.0),
                arxiv_categories=topic_data.get('arxiv_categories')
            ))
        
        return DomainTemplate(
            domain=data['domain'],
            description=data.get('description', ''),
            sources=sources,
            topics=topics,
            relevance_threshold=data.get('relevance_threshold', 0.3),
            days_lookback=data.get('days_lookback', 7),
            max_papers_per_scan=data.get('max_papers_per_scan', 50)
        )
    
    def save_template(self, name: str, template: DomainTemplate):
        """
        Save a template to disk
        
        Args:
            name: Template filename without .yaml extension
            template: DomainTemplate object to save
        """
        template_path = self.templates_dir / f"{name}.yaml"
        
        # Convert to dict
        data = {
            'domain': template.domain,
            'description': template.description,
            'sources': {},
            'topics': [],
            'relevance_threshold': template.relevance_threshold,
            'days_lookback': template.days_lookback,
            'max_papers_per_scan': template.max_papers_per_scan
        }
        
        # Convert sources
        for source_name, source_config in template.sources.items():
            source_dict = {'enabled': source_config.enabled}
            if source_config.queries:
                source_dict['queries'] = source_config.queries
            if source_config.categories:
                source_dict['categories'] = source_config.categories
            if source_config.mesh_terms:
                source_dict['mesh_terms'] = source_config.mesh_terms
            if source_config.subjects:
                source_dict['subjects'] = source_config.subjects
            data['sources'][source_name] = source_dict
        
        # Convert topics
        for topic in template.topics:
            topic_dict = {
                'name': topic.name,
                'keywords': topic.keywords,
                'weight': topic.weight
            }
            if topic.arxiv_categories:
                topic_dict['arxiv_categories'] = topic.arxiv_categories
            data['topics'].append(topic_dict)
        
        # Save to file
        with open(template_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def create_custom_template(
        self,
        domain: str,
        description: str,
        base_template: str = None
    ) -> DomainTemplate:
        """
        Create a new custom template, optionally based on existing one
        
        Args:
            domain: Name of the research domain
            description: Description of the domain
            base_template: Optional template to use as starting point
            
        Returns:
            New DomainTemplate object
        """
        if base_template:
            template = self.load_template(base_template)
            template.domain = domain
            template.description = description
            return template
        else:
            # Create blank template
            return DomainTemplate(
                domain=domain,
                description=description,
                sources={
                    'arxiv': SourceConfig(enabled=False),
                    'huggingface': SourceConfig(enabled=False),
                    'pubmed': SourceConfig(enabled=False)
                },
                topics=[]
            )
    
    def get_template_info(self, name: str) -> Dict:
        """
        Get summary information about a template without fully loading it
        
        Args:
            name: Template name
            
        Returns:
            Dict with summary info
        """
        template_path = self.templates_dir / f"{name}.yaml"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template '{name}' not found")
        
        with open(template_path) as f:
            data = yaml.safe_load(f)
        
        enabled_sources = [
            source for source, config in data.get('sources', {}).items()
            if config.get('enabled', False)
        ]
        
        return {
            'domain': data.get('domain', 'Unknown'),
            'description': data.get('description', ''),
            'num_topics': len(data.get('topics', [])),
            'enabled_sources': enabled_sources,
            'relevance_threshold': data.get('relevance_threshold', 0.3)
        }


if __name__ == "__main__":
    # Test the template manager
    manager = TemplateManager()
    
    print("Available Templates:")
    for template in manager.list_templates():
        print(f"  - {template['name']}: {template['domain']}")
        print(f"    {template['description']}")
