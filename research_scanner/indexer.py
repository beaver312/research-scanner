"""
ChromaDB indexer for research papers.
Stores papers and their summaries in a dedicated collection within the
same ChromaDB instance used by Scholars Terminal for books.
"""

import json
import logging
import re
from datetime import datetime
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from research_scanner.models import Paper, PaperSummary, ScanHistory
from research_scanner.config import ScannerConfig

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into chunks of approximately `chunk_size` tokens.
    Uses simple word-based splitting (roughly 1 token ≈ 0.75 words).
    """
    if not text or not text.strip():
        return []

    words = text.split()
    # Approximate tokens: 1 token ≈ 0.75 words, so chunk_size tokens ≈ chunk_size * 0.75 words
    words_per_chunk = int(chunk_size * 0.75)
    overlap_words = int(overlap * 0.75)

    if len(words) <= words_per_chunk:
        return [text.strip()]

    chunks = []
    start = 0
    while start < len(words):
        end = start + words_per_chunk
        chunk = " ".join(words[start:end])
        chunks.append(chunk.strip())
        start = end - overlap_words  # Overlap for context continuity

    return chunks


class ResearchIndexer:
    """Index research papers into ChromaDB."""

    def __init__(self, config: ScannerConfig):
        self.config = config
        self.client = None
        self.collection = None
        self.history = ScanHistory.load(config.scan_history_path)

        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB is not installed. Run: pip install chromadb")
            return

        self._init_chromadb()

    def _init_chromadb(self):
        """Initialize ChromaDB connection and collection."""
        try:
            self.client = chromadb.PersistentClient(
                path=self.config.vector_db_path,
                settings=Settings(anonymized_telemetry=False),
            )

            # Create or get the research papers collection
            self.collection = self.client.get_or_create_collection(
                name=self.config.research_collection_name,
                metadata={
                    "description": "AI research papers indexed by Scholars Terminal Research Scanner",
                    "hnsw:space": "cosine",
                },
            )

            count = self.collection.count()
            logger.info(
                f"ChromaDB research collection '{self.config.research_collection_name}' "
                f"initialized with {count} existing documents"
            )

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collection = None

    def is_ready(self) -> bool:
        """Check if the indexer is properly initialized."""
        return self.collection is not None

    def is_paper_indexed(self, paper_id: str) -> bool:
        """Check if a paper has already been indexed."""
        return self.history.is_known(paper_id)

    def index_paper(self, paper: Paper, summary: PaperSummary) -> bool:
        """
        Index a single paper with its summary into ChromaDB.
        Creates multiple chunks for the paper content.
        """
        if not self.is_ready():
            logger.error("ChromaDB not initialized, cannot index paper")
            return False

        if self.is_paper_indexed(paper.paper_id):
            logger.debug(f"Paper already indexed: {paper.paper_id}")
            return False

        try:
            # Build the full text to index
            content_parts = [
                f"Title: {paper.title}",
                f"Authors: {', '.join(paper.authors)}",
                f"Source: {paper.source}",
                f"Published: {paper.published_date.strftime('%Y-%m-%d')}",
                f"\nAbstract:\n{paper.abstract}",
            ]

            if summary.summary:
                content_parts.append(f"\nAI Summary:\n{summary.summary}")

            if summary.key_findings:
                findings = "\n".join(f"- {f}" for f in summary.key_findings)
                content_parts.append(f"\nKey Findings:\n{findings}")

            if summary.methodology:
                content_parts.append(f"\nMethodology:\n{summary.methodology}")

            if summary.results:
                content_parts.append(f"\nResults:\n{summary.results}")

            if paper.full_text:
                content_parts.append(f"\nFull Text:\n{paper.full_text}")

            full_content = "\n".join(content_parts)
            chunks = chunk_text(full_content, self.config.chunk_size, self.config.chunk_overlap)

            if not chunks:
                logger.warning(f"No chunks generated for paper: {paper.title[:60]}")
                return False

            # Build metadata (ChromaDB requires flat string/int/float values)
            base_metadata = {
                "paper_id": paper.paper_id,
                "title": paper.title[:500],
                "authors": ", ".join(paper.authors[:5]),
                "source": paper.source,
                "url": paper.url,
                "pdf_url": paper.pdf_url,
                "published_date": paper.published_date.isoformat(),
                "categories": ", ".join(paper.categories[:5]),
                "citation_count": paper.citation_count,
                "relevance_score": summary.relevance_score,
                "topics": ", ".join(summary.topics[:5]),
                "content_type": "research_paper",
                "indexed_at": datetime.now().isoformat(),
                "summary_excerpt": summary.summary[:300] if summary.summary else "",
            }

            # Add chunks to ChromaDB
            ids = [f"{paper.paper_id}__chunk_{i}" for i in range(len(chunks))]
            metadatas = []
            for i in range(len(chunks)):
                meta = base_metadata.copy()
                meta["chunk_index"] = i
                meta["total_chunks"] = len(chunks)
                metadatas.append(meta)

            self.collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas,
            )

            # Track in history
            self.history.mark_known(paper.paper_id)
            self.history.save(self.config.scan_history_path)

            logger.info(f"Indexed paper '{paper.title[:60]}' ({len(chunks)} chunks)")
            return True

        except Exception as e:
            logger.error(f"Failed to index paper '{paper.title[:60]}': {e}")
            return False

    def index_batch(self, papers_and_summaries: list[tuple[Paper, PaperSummary]]) -> dict:
        """
        Index a batch of papers. Returns stats dict.
        """
        stats = {"total": len(papers_and_summaries), "indexed": 0, "skipped": 0, "errors": 0}

        for paper, summary in papers_and_summaries:
            if self.is_paper_indexed(paper.paper_id):
                stats["skipped"] += 1
                continue
            try:
                if self.index_paper(paper, summary):
                    stats["indexed"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Batch index error for '{paper.title[:40]}': {e}")

        logger.info(
            f"Batch index complete: {stats['indexed']} indexed, "
            f"{stats['skipped']} skipped, {stats['errors']} errors"
        )
        return stats

    def search_papers(self, query: str, n_results: int = 10) -> list[dict]:
        """Search indexed research papers."""
        if not self.is_ready():
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"content_type": "research_paper"},
            )

            papers = []
            seen_ids = set()
            for i, doc_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i]
                paper_id = meta.get("paper_id", "")

                # Deduplicate by paper_id (multiple chunks per paper)
                if paper_id in seen_ids:
                    continue
                seen_ids.add(paper_id)

                papers.append({
                    "paper_id": paper_id,
                    "title": meta.get("title", ""),
                    "authors": meta.get("authors", ""),
                    "source": meta.get("source", ""),
                    "url": meta.get("url", ""),
                    "published_date": meta.get("published_date", ""),
                    "relevance_score": meta.get("relevance_score", 0),
                    "topics": meta.get("topics", ""),
                    "summary_excerpt": meta.get("summary_excerpt", ""),
                    "content_excerpt": results["documents"][0][i][:300],
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                })

            return papers

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_latest_papers(self, n: int = 20) -> list[dict]:
        """Get the most recently indexed papers."""
        if not self.is_ready():
            return []

        try:
            # ChromaDB doesn't support ORDER BY, so we fetch more and sort
            results = self.collection.get(
                where={"content_type": "research_paper"},
                limit=n * 3,  # Fetch extra due to chunks
                include=["metadatas"],
            )

            seen_ids = set()
            papers = []
            for meta in results["metadatas"]:
                pid = meta.get("paper_id", "")
                if pid in seen_ids or meta.get("chunk_index", 0) != 0:
                    continue
                seen_ids.add(pid)
                papers.append(meta)

            # Sort by indexed_at descending
            papers.sort(key=lambda x: x.get("indexed_at", ""), reverse=True)
            return papers[:n]

        except Exception as e:
            logger.error(f"get_latest_papers failed: {e}")
            return []

    def get_stats(self) -> dict:
        """Get collection statistics."""
        if not self.is_ready():
            return {"status": "not_initialized"}

        return {
            "status": "ready",
            "total_documents": self.collection.count(),
            "total_papers_tracked": self.history.total_papers_indexed,
            "known_paper_ids": len(self.history.known_paper_ids),
            "last_scan_times": {
                k: v.isoformat() for k, v in self.history.last_scan_times.items()
            },
        }
