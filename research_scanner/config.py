"""
Configuration for the Research Scanner.
Edit this file to customize topics, sources, and behavior.
Can load from domain templates or use defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


@dataclass
class TopicConfig:
    """A topic of interest with search keywords and weight."""
    name: str
    keywords: list[str]
    weight: float = 1.0  # Higher = more likely to be fetched/summarized
    arxiv_categories: list[str] = field(default_factory=list)


# ── Default interest topics ──────────────────────────────────────────
DEFAULT_TOPICS = [
    TopicConfig(
        name="Retrieval-Augmented Generation",
        keywords=["RAG", "retrieval augmented generation", "retrieval-augmented"],
        weight=1.5,
        arxiv_categories=["cs.CL", "cs.IR"],
    ),
    TopicConfig(
        name="Embeddings & Vector Search",
        keywords=["embeddings", "vector search", "semantic search", "vector database"],
        weight=1.3,
        arxiv_categories=["cs.CL", "cs.IR"],
    ),
    TopicConfig(
        name="AI Agents",
        keywords=["AI agents", "autonomous agents", "tool use", "agent framework", "agentic"],
        weight=1.4,
        arxiv_categories=["cs.AI", "cs.MA"],
    ),
    TopicConfig(
        name="Transformers & LLMs",
        keywords=["transformer", "large language model", "LLM", "attention mechanism", "fine-tuning"],
        weight=1.0,
        arxiv_categories=["cs.CL", "cs.LG"],
    ),
    TopicConfig(
        name="Multimodal AI",
        keywords=["multimodal", "vision language", "image text", "VLM"],
        weight=1.0,
        arxiv_categories=["cs.CV", "cs.CL"],
    ),
    TopicConfig(
        name="Reasoning & Chain-of-Thought",
        keywords=["reasoning", "chain of thought", "step by step", "logical reasoning", "CoT"],
        weight=1.2,
        arxiv_categories=["cs.AI", "cs.CL"],
    ),
    TopicConfig(
        name="Small & Efficient Models",
        keywords=["distillation", "quantization", "pruning", "efficient inference", "small language model", "SLM"],
        weight=1.3,
        arxiv_categories=["cs.LG", "cs.CL"],
    ),
    TopicConfig(
        name="Code Generation",
        keywords=["code generation", "code LLM", "programming", "software engineering AI"],
        weight=1.1,
        arxiv_categories=["cs.SE", "cs.CL"],
    ),
    # ── PubMed-focused topics ────────────────────────────────────
    TopicConfig(
        name="Neuroscience & Cognition",
        keywords=["neuroscience", "cognitive", "brain", "neural", "consciousness"],
        weight=1.2,
        arxiv_categories=[],  # PubMed doesn't use arXiv categories
    ),
    TopicConfig(
        name="AI in Healthcare",
        keywords=["medical AI", "clinical decision", "diagnostic", "healthcare AI"],
        weight=1.1,
        arxiv_categories=["cs.CY"],
    ),
    TopicConfig(
        name="Computational Biology",
        keywords=["bioinformatics", "computational biology", "genomics", "protein"],
        weight=1.0,
        arxiv_categories=["q-bio"],
    ),
]


@dataclass
class ScannerConfig:
    """Master configuration for the Research Scanner."""

    # ── Paths (defaults for VSCMS HomeLab) ────────────────────────
    project_root: str = r"D:\Claude\Projects\scholars-terminal"
    vector_db_path: str = ""  # Auto-set from project_root if empty
    scan_history_path: str = ""  # Auto-set from project_root if empty
    paper_cache_dir: str = ""  # Auto-set from project_root if empty

    # ── Ollama ────────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"  # Adjust to whatever model you're running
    ollama_timeout: int = 300  # 5 minutes, matching Scholars_api.py

    # ── ChromaDB ──────────────────────────────────────────────────
    research_collection_name: str = "research_papers"
    embedding_model: str = "all-MiniLM-L6-v2"  # Same as existing Scholars Terminal
    chunk_size: int = 500  # Tokens per chunk
    chunk_overlap: int = 50

    # ── Sources ───────────────────────────────────────────────────
    arxiv_enabled: bool = True
    arxiv_max_results_per_query: int = 20
    arxiv_rate_limit_seconds: float = 3.0  # arXiv policy: 1 req per 3 sec

    semantic_scholar_enabled: bool = False  # Disabled - requires academic/corporate email for API key
    semantic_scholar_max_results: int = 20
    semantic_scholar_api_key: str = field(default_factory=lambda: os.getenv("SEMANTIC_SCHOLAR_API_KEY", ""))

    huggingface_enabled: bool = True
    huggingface_max_results: int = 30

    # PubMed (biomedical literature)
    pubmed_enabled: bool = True
    pubmed_max_results: int = 20
    pubmed_email: str = "scholar@example.com"  # NCBI requires an email (any email works)
    pubmed_api_key: str = ""  # Optional: get free key for 10 req/sec instead of 3

    # ── Scanning behavior ─────────────────────────────────────────
    days_lookback: int = 7  # How far back to look on each scan
    relevance_threshold: float = 0.3  # 0.0-1.0, papers below this are skipped
    max_papers_per_scan: int = 50  # Safety cap per scan run
    fetch_full_text: bool = False  # PDF download + extraction (slow, disk-heavy)

    # ── Scheduling ────────────────────────────────────────────────
    schedule_enabled: bool = True
    schedule_cron: str = "0 3 * * *"  # Daily at 3 AM
    schedule_on_startup: bool = True  # Run a scan when the service starts

    # ── Topics ────────────────────────────────────────────────────
    topics: list[TopicConfig] = field(default_factory=lambda: DEFAULT_TOPICS.copy())

    def __post_init__(self):
        root = Path(self.project_root)
        if not self.vector_db_path:
            self.vector_db_path = str(root / "data" / "vector_db")
        if not self.scan_history_path:
            self.scan_history_path = str(root / "data" / "scan_history.json")
        if not self.paper_cache_dir:
            self.paper_cache_dir = str(root / "data" / "paper_cache")

    def get_all_arxiv_categories(self) -> list[str]:
        """Collect unique arXiv categories from all topics."""
        cats = set()
        for topic in self.topics:
            cats.update(topic.arxiv_categories)
        return sorted(cats)

    def get_all_keywords(self) -> list[str]:
        """Collect all keywords across topics."""
        kws = []
        for topic in self.topics:
            kws.extend(topic.keywords)
        return kws

    def get_topic_for_keywords(self, text: str) -> list[TopicConfig]:
        """Find which topics match a given text (title/abstract)."""
        text_lower = text.lower()
        matches = []
        for topic in self.topics:
            for kw in topic.keywords:
                if kw.lower() in text_lower:
                    matches.append(topic)
                    break
        return matches

    @classmethod
    def from_template(cls, template_name: str = "user_config") -> "ScannerConfig":
        """
        Create a ScannerConfig from a domain template.
        
        Args:
            template_name: Name of template to load (default: "user_config")
                          Use "user_config" to load the user's configured template
                          Or specify a template name like "ai_ml", "medical_cardiac", etc.
        
        Returns:
            ScannerConfig configured from the template
        """
        try:
            from research_scanner.template_manager import TemplateManager
            
            # Load template
            manager = TemplateManager()
            template = manager.load_template(template_name)
            
            # Convert template topics to TopicConfig
            topics = []
            for topic in template.topics:
                topics.append(TopicConfig(
                    name=topic.name,
                    keywords=topic.keywords,
                    weight=topic.weight,
                    arxiv_categories=topic.arxiv_categories or []
                ))
            
            # Configure sources based on template
            sources = template.sources
            arxiv_enabled = sources.get('arxiv') and sources['arxiv'].enabled
            huggingface_enabled = sources.get('huggingface') and sources['huggingface'].enabled
            pubmed_enabled = sources.get('pubmed') and sources['pubmed'].enabled
            
            # Create config with template settings
            config = cls(
                topics=topics,
                relevance_threshold=template.relevance_threshold,
                days_lookback=template.days_lookback,
                max_papers_per_scan=template.max_papers_per_scan,
                arxiv_enabled=arxiv_enabled,
                huggingface_enabled=huggingface_enabled,
                pubmed_enabled=pubmed_enabled,
            )
            
            # Store PubMed template queries if available
            if pubmed_enabled and sources.get('pubmed') and sources['pubmed'].queries:
                config._template_pubmed_queries = sources['pubmed'].queries
            
            return config
            
        except FileNotFoundError:
            # Template not found, use defaults
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Template '{template_name}' not found. Using default configuration. "
                f"Run 'python setup_wizard.py' to create your configuration."
            )
            return cls()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading template '{template_name}': {e}")
            logger.warning("Falling back to default configuration.")
            return cls()
