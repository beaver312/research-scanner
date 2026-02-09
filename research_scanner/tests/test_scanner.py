"""
Test suite for the Research Scanner.
Tests models, config, text chunking, source parsing, and summarizer logic.
Network-dependent tests are marked and can be skipped.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Paper, PaperSummary, ScanResult, ScanHistory
from config import ScannerConfig, TopicConfig, DEFAULT_TOPICS
from indexer import chunk_text


class TestPaperModel(unittest.TestCase):
    """Test the Paper data model."""

    def test_paper_creation(self):
        p = Paper(
            title="Test Paper",
            authors=["Alice", "Bob"],
            abstract="This is a test abstract.",
            source="arxiv",
            url="https://arxiv.org/abs/2401.00001",
            published_date=datetime(2025, 1, 15),
            paper_id="arxiv:2401.00001",
        )
        self.assertEqual(p.title, "Test Paper")
        self.assertEqual(p.paper_id, "arxiv:2401.00001")
        self.assertEqual(len(p.authors), 2)

    def test_paper_auto_id(self):
        """Paper should auto-generate ID if not provided."""
        p = Paper(
            title="Auto ID Test",
            authors=["Alice"],
            abstract="Test",
            source="arxiv",
            url="https://example.com",
            published_date=datetime.now(),
        )
        self.assertTrue(len(p.paper_id) > 0)
        self.assertEqual(len(p.paper_id), 16)  # SHA256[:16]

    def test_paper_deterministic_id(self):
        """Same title + source should produce same auto-ID."""
        p1 = Paper(title="Same Paper", authors=[], abstract="", source="arxiv",
                    url="", published_date=datetime.now())
        p2 = Paper(title="Same Paper", authors=[], abstract="", source="arxiv",
                    url="", published_date=datetime.now())
        self.assertEqual(p1.paper_id, p2.paper_id)

    def test_paper_different_source_different_id(self):
        p1 = Paper(title="Same Paper", authors=[], abstract="", source="arxiv",
                    url="", published_date=datetime.now())
        p2 = Paper(title="Same Paper", authors=[], abstract="", source="huggingface",
                    url="", published_date=datetime.now())
        self.assertNotEqual(p1.paper_id, p2.paper_id)

    def test_paper_serialization(self):
        p = Paper(
            title="Serialize Test",
            authors=["Alice"],
            abstract="Abstract text",
            source="arxiv",
            url="https://example.com",
            published_date=datetime(2025, 6, 1, 12, 0, 0),
            paper_id="test:001",
        )
        d = p.to_dict()
        self.assertEqual(d["title"], "Serialize Test")
        self.assertIn("2025-06-01", d["published_date"])

        # Round-trip
        p2 = Paper.from_dict(d)
        self.assertEqual(p2.title, p.title)
        self.assertEqual(p2.paper_id, p.paper_id)


class TestPaperSummary(unittest.TestCase):
    """Test the PaperSummary model."""

    def test_summary_creation(self):
        s = PaperSummary(
            paper_id="test:001",
            summary="This paper introduces a new method.",
            key_findings=["Finding 1", "Finding 2"],
            relevance_score=0.85,
            topics=["RAG", "Embeddings"],
        )
        self.assertEqual(s.relevance_score, 0.85)
        self.assertEqual(len(s.key_findings), 2)

    def test_summary_serialization(self):
        s = PaperSummary(
            paper_id="test:002",
            summary="Summary text",
            key_findings=["F1"],
            generated_at=datetime(2025, 1, 1),
        )
        d = s.to_dict()
        s2 = PaperSummary.from_dict(d)
        self.assertEqual(s2.paper_id, s.paper_id)


class TestScanResult(unittest.TestCase):
    def test_scan_result_finish(self):
        sr = ScanResult(source="arxiv")
        sr.papers_found = 10
        sr.papers_new = 5
        sr.finish()
        self.assertIsNotNone(sr.scan_end)
        self.assertGreaterEqual(sr.duration_seconds, 0)


class TestScanHistory(unittest.TestCase):
    def test_history_tracking(self):
        h = ScanHistory()
        self.assertFalse(h.is_known("paper:001"))
        h.mark_known("paper:001")
        self.assertTrue(h.is_known("paper:001"))
        self.assertEqual(h.total_papers_indexed, 1)

    def test_history_save_load(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            h = ScanHistory()
            h.mark_known("paper:001")
            h.mark_known("paper:002")
            h.update_scan_time("arxiv")
            h.save(path)

            h2 = ScanHistory.load(path)
            self.assertTrue(h2.is_known("paper:001"))
            self.assertTrue(h2.is_known("paper:002"))
            self.assertFalse(h2.is_known("paper:003"))
            self.assertEqual(h2.total_papers_indexed, 2)
            self.assertIn("arxiv", h2.last_scan_times)
        finally:
            os.unlink(path)

    def test_history_load_missing_file(self):
        h = ScanHistory.load("/tmp/nonexistent_scan_history.json")
        self.assertEqual(len(h.known_paper_ids), 0)


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        c = ScannerConfig()
        self.assertTrue(c.arxiv_enabled)
        self.assertTrue(c.semantic_scholar_enabled)
        self.assertTrue(c.huggingface_enabled)
        self.assertEqual(len(c.topics), len(DEFAULT_TOPICS))

    def test_auto_paths(self):
        c = ScannerConfig(project_root="/test/project")
        self.assertIn("vector_db", c.vector_db_path)
        self.assertIn("scan_history", c.scan_history_path)

    def test_get_all_categories(self):
        c = ScannerConfig()
        cats = c.get_all_arxiv_categories()
        self.assertIn("cs.AI", cats)
        self.assertIn("cs.CL", cats)

    def test_topic_matching(self):
        c = ScannerConfig()
        matches = c.get_topic_for_keywords("A new approach to retrieval augmented generation for LLMs")
        topic_names = [t.name for t in matches]
        self.assertIn("Retrieval-Augmented Generation", topic_names)

    def test_topic_matching_case_insensitive(self):
        c = ScannerConfig()
        matches = c.get_topic_for_keywords("RETRIEVAL AUGMENTED GENERATION")
        self.assertTrue(len(matches) > 0)


class TestChunking(unittest.TestCase):
    def test_short_text_no_chunks(self):
        chunks = chunk_text("Hello world this is a short text.")
        self.assertEqual(len(chunks), 1)

    def test_empty_text(self):
        self.assertEqual(chunk_text(""), [])
        self.assertEqual(chunk_text("   "), [])
        self.assertEqual(chunk_text(None), [])

    def test_long_text_chunks(self):
        # Generate text longer than one chunk
        words = ["word"] * 1000
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        self.assertGreater(len(chunks), 1)
        # Each chunk should have content
        for chunk in chunks:
            self.assertTrue(len(chunk.strip()) > 0)

    def test_chunk_overlap(self):
        """Chunks should overlap to preserve context."""
        words = [f"w{i}" for i in range(200)]
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        if len(chunks) >= 2:
            # Last words of chunk 0 should appear in chunk 1
            words_0 = chunks[0].split()
            words_1 = chunks[1].split()
            # There should be some overlap
            overlap_found = any(w in words_1 for w in words_0[-10:])
            self.assertTrue(overlap_found, "Expected overlap between consecutive chunks")


class TestArxivParsing(unittest.TestCase):
    """Test arXiv XML response parsing."""

    def test_parse_arxiv_entry(self):
        """Test parsing a real-format arXiv API XML entry."""
        from sources.arxiv_source import ArxivSource, ATOM_NS

        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.12345v1</id>
    <title>A Novel Approach to Retrieval-Augmented Generation</title>
    <summary>We present a new method for combining retrieval with generation in LLMs.</summary>
    <published>2025-01-15T00:00:00Z</published>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Jones</name></author>
    <link href="http://arxiv.org/abs/2401.12345v1" rel="alternate" type="text/html"/>
    <link href="http://arxiv.org/pdf/2401.12345v1" title="pdf" type="application/pdf"/>
    <arxiv:primary_category term="cs.CL"/>
    <category term="cs.CL"/>
    <category term="cs.AI"/>
  </entry>
</feed>"""

        source = ArxivSource()
        root = ET.fromstring(xml_text)
        entry = root.find(f"{ATOM_NS}entry")
        paper = source._parse_entry(entry)

        self.assertIsNotNone(paper)
        self.assertEqual(paper.title, "A Novel Approach to Retrieval-Augmented Generation")
        self.assertEqual(len(paper.authors), 2)
        self.assertEqual(paper.authors[0], "Alice Smith")
        self.assertIn("cs.CL", paper.categories)
        self.assertIn("cs.AI", paper.categories)
        self.assertEqual(paper.paper_id, "arxiv:2401.12345v1")
        self.assertIn("pdf", paper.pdf_url)

    def test_parse_empty_entry(self):
        from sources.arxiv_source import ArxivSource, ATOM_NS

        xml_text = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/0000.00000</id>
  </entry>
</feed>"""

        source = ArxivSource()
        root = ET.fromstring(xml_text)
        entry = root.find(f"{ATOM_NS}entry")
        paper = source._parse_entry(entry)
        # Should return None because title is empty
        self.assertIsNone(paper)


class TestSemanticScholarParsing(unittest.TestCase):
    """Test Semantic Scholar response parsing."""

    def test_parse_s2_paper(self):
        from sources.semantic_scholar_source import SemanticScholarSource

        data = {
            "paperId": "abc123",
            "title": "Efficient Attention Mechanisms for Transformers",
            "authors": [{"name": "Alice"}, {"name": "Bob"}],
            "abstract": "We propose a new attention mechanism.",
            "url": "https://www.semanticscholar.org/paper/abc123",
            "year": 2025,
            "publicationDate": "2025-03-15",
            "externalIds": {"ArXiv": "2503.12345", "DOI": "10.1234/test"},
            "citationCount": 42,
            "fieldsOfStudy": ["Computer Science"],
            "openAccessPdf": {"url": "https://arxiv.org/pdf/2503.12345.pdf"},
        }

        source = SemanticScholarSource()
        paper = source._parse_paper(data)

        self.assertIsNotNone(paper)
        self.assertEqual(paper.title, "Efficient Attention Mechanisms for Transformers")
        self.assertEqual(len(paper.authors), 2)
        self.assertEqual(paper.paper_id, "arxiv:2503.12345")
        self.assertEqual(paper.citation_count, 42)
        self.assertIn("Computer Science", paper.categories)

    def test_parse_s2_minimal(self):
        from sources.semantic_scholar_source import SemanticScholarSource

        data = {"paperId": "xyz", "title": "Minimal Paper", "authors": [], "year": 2024}
        source = SemanticScholarSource()
        paper = source._parse_paper(data)
        self.assertIsNotNone(paper)
        self.assertEqual(paper.paper_id, "s2:xyz")


class TestHuggingFaceParsing(unittest.TestCase):
    """Test HuggingFace paper parsing."""

    def test_parse_hf_paper(self):
        from sources.huggingface_source import HuggingFaceSource

        data = {
            "paper": {
                "id": "2501.12345",
                "title": "HF Daily Pick: New RAG Method",
                "summary": "A curated paper about RAG improvements.",
                "authors": [{"name": "Charlie"}],
                "upvotes": 15,
            },
            "publishedAt": "2025-01-20T10:00:00Z",
        }

        source = HuggingFaceSource()
        paper = source._parse_hf_paper(data)

        self.assertIsNotNone(paper)
        self.assertEqual(paper.title, "HF Daily Pick: New RAG Method")
        self.assertEqual(paper.paper_id, "arxiv:2501.12345")
        self.assertEqual(paper.citation_count, 15)  # upvotes as proxy


class TestSummarizerJsonParsing(unittest.TestCase):
    """Test the summarizer's JSON extraction from LLM responses."""

    def test_clean_json(self):
        from summarizer import PaperSummarizer
        s = PaperSummarizer(ScannerConfig())

        result = s._parse_json_response('{"relevance_score": 0.8, "matching_topics": ["RAG"]}')
        self.assertEqual(result["relevance_score"], 0.8)

    def test_json_with_markdown_fences(self):
        from summarizer import PaperSummarizer
        s = PaperSummarizer(ScannerConfig())

        text = '```json\n{"relevance_score": 0.5}\n```'
        result = s._parse_json_response(text)
        self.assertEqual(result["relevance_score"], 0.5)

    def test_json_with_preamble(self):
        from summarizer import PaperSummarizer
        s = PaperSummarizer(ScannerConfig())

        text = 'Here is my analysis:\n\n{"relevance_score": 0.9, "matching_topics": ["agents"]}'
        result = s._parse_json_response(text)
        self.assertEqual(result["relevance_score"], 0.9)

    def test_invalid_json(self):
        from summarizer import PaperSummarizer
        s = PaperSummarizer(ScannerConfig())

        result = s._parse_json_response("This is not JSON at all")
        self.assertEqual(result, {})


class TestSummarizerKeywordScoring(unittest.TestCase):
    """Test the keyword-based pre-filter in the summarizer."""

    def test_keyword_match(self):
        from summarizer import PaperSummarizer
        config = ScannerConfig()
        s = PaperSummarizer(config)

        paper = Paper(
            title="A New Approach to Retrieval-Augmented Generation",
            authors=["Test"],
            abstract="We improve RAG by combining dense retrieval with sparse methods.",
            source="arxiv",
            url="",
            published_date=datetime.now(),
        )

        # Mock Ollama to avoid network calls
        with patch.object(s, '_call_ollama', return_value='{"relevance_score": 0.9, "matching_topics": ["RAG"]}'):
            score, topics = s.score_relevance(paper)
            self.assertGreater(score, 0.0)

    def test_no_keyword_match(self):
        from summarizer import PaperSummarizer
        config = ScannerConfig()
        s = PaperSummarizer(config)

        paper = Paper(
            title="Underwater Basket Weaving in the 21st Century",
            authors=["Test"],
            abstract="A study of traditional crafts with no AI relevance.",
            source="arxiv",
            url="",
            published_date=datetime.now(),
        )

        # Should not even call Ollama since no keywords match
        score, topics = s.score_relevance(paper)
        self.assertEqual(score, 0.0)
        self.assertEqual(topics, [])


class TestBaseSourceRateLimiting(unittest.TestCase):
    """Test rate limiting in BaseSource."""

    def test_rate_limit_enforced(self):
        from sources.base_source import BaseSource
        import time

        class DummySource(BaseSource):
            def fetch_recent(self, days_back=7, max_results=20):
                return []
            def search(self, query, max_results=10):
                return []

        source = DummySource("test", rate_limit_seconds=0.1)
        start = time.time()
        source._rate_limit()
        source._rate_limit()
        elapsed = time.time() - start
        self.assertGreaterEqual(elapsed, 0.09)  # Should have waited ~0.1s


if __name__ == "__main__":
    unittest.main(verbosity=2)
