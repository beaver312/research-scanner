"""
Research Scanner — Main orchestrator.
Coordinates: fetch papers → score relevance → summarize → index into ChromaDB.
Can run as a one-shot CLI command, a scheduled daemon, or triggered via API.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for both script and module execution
_script_dir = Path(__file__).parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from research_scanner.models import Paper, PaperSummary, ScanResult, ScanHistory
from research_scanner.config import ScannerConfig
from research_scanner.summarizer import PaperSummarizer
from research_scanner.indexer import ResearchIndexer
from research_scanner.sources.arxiv_source import ArxivSource
from research_scanner.sources.semantic_scholar_source import SemanticScholarSource
from research_scanner.sources.huggingface_source import HuggingFaceSource
from research_scanner.sources.pubmed_source import PubMedSource

logger = logging.getLogger(__name__)


class ResearchScanner:
    """
    Main orchestrator for the research scanning pipeline.
    Automatically loads from user template if available.
    """

    def __init__(self, config: ScannerConfig = None):
        # Try to load from user template if no config provided
        if config is None:
            config = ScannerConfig.from_template("user_config")
        
        self.config = config
        self.summarizer = PaperSummarizer(self.config)
        self.indexer = ResearchIndexer(self.config)

        # Initialize enabled sources
        self.sources = []
        if self.config.arxiv_enabled:
            self.sources.append(ArxivSource(
                rate_limit_seconds=self.config.arxiv_rate_limit_seconds,
            ))
        if self.config.semantic_scholar_enabled:
            self.sources.append(SemanticScholarSource(
                api_key=self.config.semantic_scholar_api_key,
            ))
        if self.config.huggingface_enabled:
            self.sources.append(HuggingFaceSource())
        if self.config.pubmed_enabled:
            pubmed_source = PubMedSource(
                email=self.config.pubmed_email,
                api_key=self.config.pubmed_api_key,
            )
            # Configure template-specific queries if available
            if hasattr(self.config, '_template_pubmed_queries'):
                pubmed_source.set_template_queries(self.config._template_pubmed_queries)
            self.sources.append(pubmed_source)

        logger.info(
            f"Research Scanner initialized with {len(self.sources)} sources: "
            f"{[s.name for s in self.sources]}"
        )

    def fetch_all_papers(self) -> list[Paper]:
        """Fetch papers from all enabled sources."""
        all_papers = []
        seen_ids = set()

        for source in self.sources:
            result = ScanResult(source=source.name)
            try:
                logger.info(f"Fetching from {source.name}...")

                papers = source.fetch_by_topics(
                    topics=self.config.topics,
                    days_back=self.config.days_lookback,
                    max_results=self.config.max_papers_per_scan,
                )

                result.papers_found = len(papers)

                for paper in papers:
                    # Deduplicate across sources
                    if paper.paper_id in seen_ids:
                        result.papers_skipped += 1
                        continue

                    # Skip already indexed papers
                    if self.indexer.is_paper_indexed(paper.paper_id):
                        result.papers_skipped += 1
                        seen_ids.add(paper.paper_id)
                        continue

                    seen_ids.add(paper.paper_id)
                    all_papers.append(paper)
                    result.papers_new += 1

                result.finish()
                logger.info(
                    f"[{source.name}] Found: {result.papers_found}, "
                    f"New: {result.papers_new}, Skipped: {result.papers_skipped} "
                    f"({result.duration_seconds:.1f}s)"
                )

            except Exception as e:
                result.errors.append(str(e))
                result.finish()
                logger.error(f"[{source.name}] Fetch failed: {e}")

        logger.info(f"Total unique new papers: {len(all_papers)}")
        return all_papers

    def run_scan(self) -> dict:
        """
        Execute the full scan pipeline:
        1. Fetch new papers from all sources
        2. Score relevance and filter
        3. Generate summaries
        4. Index into ChromaDB
        Returns a results summary dict.
        """
        scan_start = datetime.now()
        results = {
            "scan_start": scan_start.isoformat(),
            "papers_fetched": 0,
            "papers_relevant": 0,
            "papers_indexed": 0,
            "papers_skipped": 0,
            "errors": [],
            "source_stats": {},
        }

        try:
            # Step 1: Fetch
            logger.info("=" * 60)
            logger.info("STEP 1: Fetching papers from sources...")
            logger.info("=" * 60)
            papers = self.fetch_all_papers()
            results["papers_fetched"] = len(papers)

            if not papers:
                logger.info("No new papers found. Scan complete.")
                results["scan_end"] = datetime.now().isoformat()
                return results

            # Step 2 & 3: Score relevance + Summarize
            logger.info("=" * 60)
            logger.info("STEP 2: Scoring relevance and generating summaries...")
            logger.info("=" * 60)
            processed = self.summarizer.process_papers(papers)
            results["papers_relevant"] = len(processed)

            if not processed:
                logger.info("No papers met relevance threshold. Scan complete.")
                results["scan_end"] = datetime.now().isoformat()
                return results

            # Step 4: Index
            logger.info("=" * 60)
            logger.info("STEP 3: Indexing into ChromaDB...")
            logger.info("=" * 60)
            index_stats = self.indexer.index_batch(processed)
            results["papers_indexed"] = index_stats["indexed"]
            results["papers_skipped"] = index_stats["skipped"]

            # Update scan times
            for source in self.sources:
                self.indexer.history.update_scan_time(source.name)
            self.indexer.history.save(self.config.scan_history_path)

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            results["errors"].append(str(e))

        scan_end = datetime.now()
        results["scan_end"] = scan_end.isoformat()
        results["duration_seconds"] = (scan_end - scan_start).total_seconds()

        logger.info("=" * 60)
        logger.info("SCAN COMPLETE")
        logger.info(
            f"Fetched: {results['papers_fetched']}, "
            f"Relevant: {results['papers_relevant']}, "
            f"Indexed: {results['papers_indexed']}, "
            f"Duration: {results.get('duration_seconds', 0):.1f}s"
        )
        logger.info("=" * 60)

        return results

    def get_status(self) -> dict:
        """Get scanner status for the API."""
        return {
            "sources_enabled": [s.name for s in self.sources],
            "topics": [t.name for t in self.config.topics],
            "relevance_threshold": self.config.relevance_threshold,
            "indexer": self.indexer.get_stats(),
            "config": {
                "days_lookback": self.config.days_lookback,
                "max_papers_per_scan": self.config.max_papers_per_scan,
                "schedule_enabled": self.config.schedule_enabled,
                "schedule_cron": self.config.schedule_cron,
                "ollama_model": self.config.ollama_model,
            },
        }


def setup_logging(verbose: bool = False):
    """Configure logging for CLI usage."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scholars Terminal Research Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scanner.py scan              # Run a full scan
  python scanner.py scan --verbose    # Run with debug logging
  python scanner.py status            # Show scanner status
  python scanner.py search "RAG"      # Search indexed papers
  python scanner.py test-sources      # Test source connectivity
        """,
    )
    parser.add_argument("command", choices=["scan", "status", "search", "test-sources"],
                        help="Command to execute")
    parser.add_argument("query", nargs="?", default="", help="Search query (for 'search' command)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    parser.add_argument("--project-root", default=None, help="Override project root path")
    parser.add_argument("--model", default=None, help="Override Ollama model name")
    parser.add_argument("--days", type=int, default=None, help="Override days lookback")

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Build config with any overrides
    config_kwargs = {}
    if args.project_root:
        config_kwargs["project_root"] = args.project_root
    if args.model:
        config_kwargs["ollama_model"] = args.model
    if args.days:
        config_kwargs["days_lookback"] = args.days

    config = ScannerConfig(**config_kwargs)

    # Ensure data directories exist
    os.makedirs(config.paper_cache_dir, exist_ok=True)
    os.makedirs(os.path.dirname(config.scan_history_path), exist_ok=True)

    scanner = ResearchScanner(config)

    if args.command == "scan":
        results = scanner.run_scan()
        print(json.dumps(results, indent=2))

    elif args.command == "status":
        status = scanner.get_status()
        print(json.dumps(status, indent=2))

    elif args.command == "search":
        if not args.query:
            print("Error: search command requires a query argument")
            sys.exit(1)
        results = scanner.indexer.search_papers(args.query)
        for i, paper in enumerate(results, 1):
            print(f"\n--- {i}. {paper['title']} ---")
            print(f"    Source: {paper['source']} | {paper['published_date']}")
            print(f"    URL: {paper['url']}")
            print(f"    Topics: {paper['topics']}")
            print(f"    {paper['summary_excerpt'][:200]}")

    elif args.command == "test-sources":
        print("Testing source connectivity...")
        for source in scanner.sources:
            try:
                papers = source.search("machine learning", max_results=2)
                print(f"  [OK] {source.name}: {len(papers)} papers returned")
                if papers:
                    print(f"       Example: {papers[0].title[:80]}")
            except Exception as e:
                print(f"  [FAIL] {source.name}: {e}")


if __name__ == "__main__":
    main()
