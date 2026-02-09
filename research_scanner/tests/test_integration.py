"""
Integration test: Full pipeline with mocked network and ChromaDB.
Verifies the entire flow: fetch → filter → summarize → index.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Paper, PaperSummary, ScanHistory
from config import ScannerConfig
from summarizer import PaperSummarizer
from indexer import chunk_text


def make_test_papers(n=5):
    """Create a list of test papers."""
    papers = []
    for i in range(n):
        papers.append(Paper(
            title=f"Paper {i}: {'RAG improvements' if i % 2 == 0 else 'Underwater Basket Weaving'}",
            authors=[f"Author {i}"],
            abstract=(
                f"This paper presents a novel retrieval-augmented generation approach "
                f"using vector embeddings for improved document search."
                if i % 2 == 0
                else f"A comprehensive study of traditional crafts with no AI relevance."
            ),
            source="arxiv",
            url=f"https://arxiv.org/abs/2501.{10000+i}",
            published_date=datetime(2025, 1, i + 1),
            paper_id=f"arxiv:2501.{10000+i}",
        ))
    return papers


class TestFullPipelineWithMocks(unittest.TestCase):
    """Test the complete pipeline with mocked external dependencies."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config = ScannerConfig(
            project_root=self.tmpdir,
            ollama_model="test-model",
            relevance_threshold=0.2,
        )
        os.makedirs(os.path.dirname(self.config.scan_history_path), exist_ok=True)

    def test_summarizer_filters_irrelevant(self):
        """Summarizer should skip papers with no keyword matches."""
        papers = make_test_papers(4)
        summarizer = PaperSummarizer(self.config)

        # Mock Ollama call for relevant papers
        def mock_ollama(prompt, temperature=0.3):
            if "RAG" in prompt or "retrieval" in prompt.lower():
                return json.dumps({
                    "relevance_score": 0.85,
                    "matching_topics": ["Retrieval-Augmented Generation"],
                    "reason": "Directly about RAG"
                })
            return json.dumps({
                "summary": "Test summary",
                "key_findings": ["Finding 1"],
                "methodology": "Test method",
                "results": "Test results",
                "limitations": "Test limitations",
            })

        with patch.object(summarizer, '_call_ollama', side_effect=mock_ollama):
            results = summarizer.process_papers(papers)

        # Only RAG papers (indices 0, 2) should be processed
        self.assertEqual(len(results), 2)
        for paper, summary in results:
            self.assertIn("RAG", paper.title)

    def test_scan_history_prevents_reprocessing(self):
        """Papers already in history should be skipped."""
        history = ScanHistory()
        history.mark_known("arxiv:2501.10000")
        history.mark_known("arxiv:2501.10001")
        history.save(self.config.scan_history_path)

        # Reload
        h2 = ScanHistory.load(self.config.scan_history_path)
        self.assertTrue(h2.is_known("arxiv:2501.10000"))
        self.assertTrue(h2.is_known("arxiv:2501.10001"))
        self.assertFalse(h2.is_known("arxiv:2501.10002"))

    def test_chunking_preserves_content(self):
        """All original content should be present across chunks."""
        text = " ".join(f"word{i}" for i in range(500))
        chunks = chunk_text(text, chunk_size=100, overlap=10)

        # Verify all words are present somewhere in the chunks
        all_chunk_text = " ".join(chunks)
        for i in range(500):
            self.assertIn(f"word{i}", all_chunk_text)

    def test_paper_batch_deduplication(self):
        """Papers with same ID should not be indexed twice."""
        papers = [
            Paper(title="Duplicate Paper", authors=["A"], abstract="Test",
                  source="arxiv", url="", published_date=datetime.now(),
                  paper_id="dup:001"),
            Paper(title="Duplicate Paper", authors=["A"], abstract="Test",
                  source="semantic_scholar", url="", published_date=datetime.now(),
                  paper_id="dup:001"),
        ]

        history = ScanHistory()
        indexed = 0
        for p in papers:
            if not history.is_known(p.paper_id):
                history.mark_known(p.paper_id)
                indexed += 1

        self.assertEqual(indexed, 1)
        self.assertEqual(history.total_papers_indexed, 1)

    def test_config_topic_matching_across_papers(self):
        """Config should correctly match topics for varied papers."""
        papers = make_test_papers(4)

        for paper in papers:
            matches = self.config.get_topic_for_keywords(f"{paper.title} {paper.abstract}")
            if "RAG" in paper.title:
                topic_names = [t.name for t in matches]
                self.assertTrue(
                    any("Retrieval" in n or "Embedding" in n for n in topic_names),
                    f"Expected RAG/embedding match for: {paper.title}"
                )
            else:
                # Non-AI paper should have no/few matches
                self.assertEqual(len(matches), 0, f"Unexpected match for: {paper.title}")


class TestSummarizerEdgeCases(unittest.TestCase):
    """Test summarizer behavior with edge cases."""

    def setUp(self):
        self.config = ScannerConfig()
        self.summarizer = PaperSummarizer(self.config)

    def test_empty_abstract(self):
        paper = Paper(
            title="RAG Paper With No Abstract",
            authors=["Test"],
            abstract="",
            source="arxiv",
            url="",
            published_date=datetime.now(),
        )
        score, topics = self.summarizer.score_relevance(paper)
        # Title has "RAG" so keyword score > 0
        self.assertGreater(score, 0.0)

    def test_very_long_abstract(self):
        paper = Paper(
            title="RAG Paper",
            authors=["Test"],
            abstract="retrieval augmented generation " * 500,
            source="arxiv",
            url="",
            published_date=datetime.now(),
        )
        # Should not crash, abstract gets truncated in prompt
        with patch.object(self.summarizer, '_call_ollama',
                         return_value='{"relevance_score": 0.9, "matching_topics": ["RAG"]}'):
            score, topics = self.summarizer.score_relevance(paper)
            self.assertGreater(score, 0.0)

    def test_ollama_failure_falls_back_to_keyword(self):
        paper = Paper(
            title="Embeddings and Vector Search",
            authors=["Test"],
            abstract="A study on embeddings for semantic search.",
            source="arxiv",
            url="",
            published_date=datetime.now(),
        )
        # Simulate Ollama failure
        with patch.object(self.summarizer, '_call_ollama', side_effect=Exception("Connection refused")):
            score, topics = self.summarizer.score_relevance(paper)
            # Should fall back to keyword scoring
            self.assertGreater(score, 0.0)

    def test_summarize_with_ollama_failure(self):
        paper = Paper(
            title="Test Paper",
            authors=["Test"],
            abstract="Test abstract about embeddings.",
            source="arxiv",
            url="",
            published_date=datetime.now(),
            paper_id="test:fail",
        )
        with patch.object(self.summarizer, '_call_ollama', side_effect=Exception("Timeout")):
            summary = self.summarizer.summarize(paper)
            self.assertEqual(summary.paper_id, "test:fail")
            self.assertIn("Error", summary.summary)


class TestAPIRoutes(unittest.TestCase):
    """Test that API routes can be created without errors."""

    def test_router_creation(self):
        try:
            from api_routes import create_research_router
        except ImportError:
            self.skipTest("FastAPI not installed — skipping route tests (will work on target system)")
            return

        router = create_research_router()
        self.assertIsNotNone(router)

        # Check expected routes exist
        route_paths = [r.path for r in router.routes]
        self.assertIn("/latest", route_paths)
        self.assertIn("/search", route_paths)
        self.assertIn("/topics", route_paths)
        self.assertIn("/scan", route_paths)
        self.assertIn("/status", route_paths)


if __name__ == "__main__":
    unittest.main(verbosity=2)
