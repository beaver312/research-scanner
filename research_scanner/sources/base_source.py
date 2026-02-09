"""
Abstract base class for research paper sources.
Provides rate limiting, retry logic, and a common interface.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime

from research_scanner.models import Paper

logger = logging.getLogger(__name__)


class BaseSource(ABC):
    """Base class for all paper sources."""

    def __init__(self, name: str, rate_limit_seconds: float = 1.0, max_retries: int = 3):
        self.name = name
        self.rate_limit_seconds = rate_limit_seconds
        self.max_retries = max_retries
        self._last_request_time: float = 0.0

    def _rate_limit(self):
        """Enforce minimum delay between requests."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            sleep_time = self.rate_limit_seconds - elapsed
            logger.debug(f"[{self.name}] Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    async def _async_rate_limit(self):
        """Async version of rate limiting."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            sleep_time = self.rate_limit_seconds - elapsed
            logger.debug(f"[{self.name}] Rate limiting: sleeping {sleep_time:.1f}s")
            await asyncio.sleep(sleep_time)
        self._last_request_time = time.time()

    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute a function with exponential backoff on failure."""
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                return func(*args, **kwargs)
            except Exception as e:
                wait = 2 ** attempt
                logger.warning(
                    f"[{self.name}] Attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                    f"Retrying in {wait}s..."
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait)
                else:
                    logger.error(f"[{self.name}] All {self.max_retries} attempts failed.")
                    raise

    @abstractmethod
    def fetch_recent(self, days_back: int = 7, max_results: int = 20) -> list[Paper]:
        """Fetch recently published papers."""
        pass

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> list[Paper]:
        """Search for papers matching a query."""
        pass

    def fetch_by_topics(self, topics: list, days_back: int = 7, max_results: int = 50) -> list[Paper]:
        """
        Fetch papers matching a list of TopicConfig objects.
        Deduplicates by paper_id.
        """
        seen_ids = set()
        all_papers = []

        for topic in topics:
            for keyword in topic.keywords:
                try:
                    papers = self.search(keyword, max_results=max_results // len(topics))
                    for paper in papers:
                        if paper.paper_id not in seen_ids:
                            seen_ids.add(paper.paper_id)
                            all_papers.append(paper)
                except Exception as e:
                    logger.error(f"[{self.name}] Error fetching topic '{topic.name}' keyword '{keyword}': {e}")

            if len(all_papers) >= max_results:
                break

        logger.info(f"[{self.name}] Fetched {len(all_papers)} unique papers across {len(topics)} topics")
        return all_papers[:max_results]
