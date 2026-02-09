"""
Data models for the Research Scanner.
Uses dataclasses for clean serialization and type safety.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import hashlib
import json


@dataclass
class Paper:
    """Represents a research paper from any source."""
    title: str
    authors: list[str]
    abstract: str
    source: str  # "arxiv", "semantic_scholar", "huggingface"
    url: str
    published_date: datetime
    paper_id: str = ""
    pdf_url: str = ""
    full_text: str = ""
    categories: list[str] = field(default_factory=list)
    citation_count: int = 0

    def __post_init__(self):
        if not self.paper_id:
            hash_input = f"{self.title.lower().strip()}:{self.source}"
            self.paper_id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["published_date"] = self.published_date.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Paper":
        data = data.copy()
        if isinstance(data.get("published_date"), str):
            data["published_date"] = datetime.fromisoformat(data["published_date"])
        return cls(**data)


@dataclass
class PaperSummary:
    """AI-generated summary of a research paper."""
    paper_id: str
    summary: str
    key_findings: list[str]
    methodology: str = ""
    results: str = ""
    limitations: str = ""
    relevance_score: float = 0.0
    topics: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    model_used: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["generated_at"] = self.generated_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "PaperSummary":
        data = data.copy()
        if isinstance(data.get("generated_at"), str):
            data["generated_at"] = datetime.fromisoformat(data["generated_at"])
        return cls(**data)


@dataclass
class ScanResult:
    """Result of a single scan operation."""
    source: str
    papers_found: int = 0
    papers_new: int = 0
    papers_indexed: int = 0
    papers_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    scan_start: datetime = field(default_factory=datetime.now)
    scan_end: Optional[datetime] = None
    duration_seconds: float = 0.0

    def finish(self):
        self.scan_end = datetime.now()
        self.duration_seconds = (self.scan_end - self.scan_start).total_seconds()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["scan_start"] = self.scan_start.isoformat()
        d["scan_end"] = self.scan_end.isoformat() if self.scan_end else None
        return d


@dataclass
class ScanHistory:
    """Tracks what has been scanned to avoid reprocessing."""
    known_paper_ids: set[str] = field(default_factory=set)
    last_scan_times: dict[str, datetime] = field(default_factory=dict)
    total_papers_indexed: int = 0

    def is_known(self, paper_id: str) -> bool:
        return paper_id in self.known_paper_ids

    def mark_known(self, paper_id: str):
        self.known_paper_ids.add(paper_id)
        self.total_papers_indexed += 1

    def update_scan_time(self, source: str):
        self.last_scan_times[source] = datetime.now()

    def save(self, path: str):
        data = {
            "known_paper_ids": list(self.known_paper_ids),
            "last_scan_times": {k: v.isoformat() for k, v in self.last_scan_times.items()},
            "total_papers_indexed": self.total_papers_indexed,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "ScanHistory":
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return cls(
                known_paper_ids=set(data.get("known_paper_ids", [])),
                last_scan_times={
                    k: datetime.fromisoformat(v)
                    for k, v in data.get("last_scan_times", {}).items()
                },
                total_papers_indexed=data.get("total_papers_indexed", 0),
            )
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()
