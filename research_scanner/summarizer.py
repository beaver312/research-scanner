"""
Paper summarizer using local Ollama instance.
Two-pass approach:
  1. Quick relevance scoring from abstract
  2. Full structured summary for papers above threshold
"""

import json
import logging
import urllib.request
from datetime import datetime

from research_scanner.models import Paper, PaperSummary
from research_scanner.config import ScannerConfig, TopicConfig

logger = logging.getLogger(__name__)


RELEVANCE_PROMPT = """You are a research paper relevance scorer. Given a paper title and abstract,
score its relevance to the following AI research topics on a scale of 0.0 to 1.0.

Topics of interest:
{topics}

Paper Title: {title}
Paper Abstract: {abstract}

Respond with ONLY a JSON object in this exact format (no other text):
{{"relevance_score": 0.0, "matching_topics": ["topic1", "topic2"], "reason": "brief reason"}}"""


SUMMARY_PROMPT = """You are an expert AI research summarizer. Provide a structured summary of this paper.

Paper Title: {title}
Authors: {authors}
Abstract: {abstract}
{full_text_section}

Respond with ONLY a JSON object in this exact format (no other text):
{{
    "summary": "A 2-3 paragraph summary of the paper's contributions and significance",
    "key_findings": ["finding 1", "finding 2", "finding 3"],
    "methodology": "Brief description of the approach/method used",
    "results": "Key quantitative or qualitative results",
    "limitations": "Notable limitations or future work mentioned"
}}"""


class PaperSummarizer:
    """Summarize research papers using a local Ollama instance."""

    def __init__(self, config: ScannerConfig):
        self.config = config
        self.ollama_url = f"{config.ollama_base_url}/api/generate"

    def _call_ollama(self, prompt: str, temperature: float = 0.3) -> str:
        """Send a prompt to Ollama and return the response text."""
        payload = json.dumps({
            "model": self.config.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 1024,
            },
            "keep_alive": "10m",
        }).encode("utf-8")

        req = urllib.request.Request(
            self.ollama_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=self.config.ollama_timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            raise

    def _parse_json_response(self, text: str) -> dict:
        """Extract and parse JSON from Ollama's response, handling common issues."""
        text = text.strip()

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in the response
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    continue

        # Try removing markdown code fences
        if "```" in text:
            lines = text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            if json_lines:
                try:
                    return json.loads("\n".join(json_lines))
                except json.JSONDecodeError:
                    pass

        logger.warning(f"Could not parse JSON from Ollama response: {text[:200]}...")
        return {}

    def score_relevance(self, paper: Paper, topics: list[TopicConfig] = None) -> tuple[float, list[str]]:
        """
        Quick relevance scoring from abstract.
        Returns (score, matching_topic_names).
        """
        if topics is None:
            topics = self.config.topics

        topics_str = "\n".join(
            f"- {t.name}: {', '.join(t.keywords)}" for t in topics
        )

        # First do a fast keyword check before hitting Ollama
        text = f"{paper.title} {paper.abstract}".lower()
        keyword_matches = []
        keyword_score = 0.0
        for topic in topics:
            for kw in topic.keywords:
                if kw.lower() in text:
                    keyword_matches.append(topic.name)
                    keyword_score += 0.15 * topic.weight
                    break

        # If no keywords match at all, skip Ollama call
        if keyword_score == 0.0:
            return 0.0, []

        # If strong keyword match, use Ollama for refined scoring
        try:
            prompt = RELEVANCE_PROMPT.format(
                topics=topics_str,
                title=paper.title,
                abstract=paper.abstract[:1000],  # Truncate long abstracts
            )
            response_text = self._call_ollama(prompt, temperature=0.1)
            result = self._parse_json_response(response_text)

            score = float(result.get("relevance_score", keyword_score))
            matching = result.get("matching_topics", keyword_matches)
            score = max(0.0, min(1.0, score))  # Clamp

            logger.debug(f"Relevance for '{paper.title[:60]}': {score:.2f} ({matching})")
            return score, matching

        except Exception as e:
            logger.warning(f"Ollama relevance scoring failed, using keyword score: {e}")
            return min(keyword_score, 1.0), keyword_matches

    def summarize(self, paper: Paper) -> PaperSummary:
        """Generate a full structured summary of a paper."""
        authors_str = ", ".join(paper.authors[:5])
        if len(paper.authors) > 5:
            authors_str += f" et al. ({len(paper.authors)} total)"

        full_text_section = ""
        if paper.full_text:
            # Use first ~2000 chars of full text beyond abstract
            full_text_section = f"\nFull Text (excerpt):\n{paper.full_text[:2000]}"

        try:
            prompt = SUMMARY_PROMPT.format(
                title=paper.title,
                authors=authors_str,
                abstract=paper.abstract,
                full_text_section=full_text_section,
            )
            response_text = self._call_ollama(prompt, temperature=0.3)
            result = self._parse_json_response(response_text)

            if not result:
                # Fallback: create a basic summary from the abstract
                return PaperSummary(
                    paper_id=paper.paper_id,
                    summary=f"[Auto-fallback] {paper.abstract[:500]}",
                    key_findings=["Summary generation failed - see abstract"],
                    model_used=self.config.ollama_model,
                    generated_at=datetime.now(),
                )

            # Score relevance too if not already done
            _, topics = self.score_relevance(paper)

            return PaperSummary(
                paper_id=paper.paper_id,
                summary=result.get("summary", paper.abstract[:500]),
                key_findings=result.get("key_findings", []),
                methodology=result.get("methodology", ""),
                results=result.get("results", ""),
                limitations=result.get("limitations", ""),
                topics=topics,
                model_used=self.config.ollama_model,
                generated_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Summary generation failed for '{paper.title[:60]}': {e}")
            return PaperSummary(
                paper_id=paper.paper_id,
                summary=f"[Error] Could not generate summary: {e}",
                key_findings=[],
                model_used=self.config.ollama_model,
                generated_at=datetime.now(),
            )

    def process_papers(self, papers: list[Paper]) -> list[tuple[Paper, PaperSummary]]:
        """
        Two-pass processing: score relevance, then summarize top papers.
        Returns list of (paper, summary) tuples for papers above threshold.
        """
        threshold = self.config.relevance_threshold

        # Pass 1: Relevance scoring
        scored = []
        for paper in papers:
            score, topics = self.score_relevance(paper)
            if score >= threshold:
                scored.append((paper, score, topics))
                logger.info(f"  ✓ [{score:.2f}] {paper.title[:70]}")
            else:
                logger.debug(f"  ✗ [{score:.2f}] {paper.title[:70]} (below threshold)")

        # Sort by relevance score
        scored.sort(key=lambda x: x[1], reverse=True)

        # Pass 2: Full summaries for relevant papers
        results = []
        for paper, score, topics in scored[:self.config.max_papers_per_scan]:
            logger.info(f"Summarizing: {paper.title[:70]}...")
            summary = self.summarize(paper)
            summary.relevance_score = score
            summary.topics = topics
            results.append((paper, summary))

        logger.info(f"Processed {len(results)}/{len(papers)} papers (threshold={threshold})")
        return results
