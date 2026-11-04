"""Shared contract between pipeline stages. See CLAUDE.md before editing.

Rule: only ADD optional fields. Renames/removals need both devs to agree.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    created = "created"
    ingested = "ingested"
    analyzed = "analyzed"
    rendered = "rendered"
    captioned = "captioned"
    published = "published"
    failed = "failed"


class Platform(str, Enum):
    tiktok = "tiktok"
    instagram = "instagram"


class PostStatus(str, Enum):
    pending = "pending"
    scheduled = "scheduled"
    uploaded_draft = "uploaded_draft"  # TikTok inbox: human adds sound + publishes in app
    published = "published"
    failed = "failed"


class Post(BaseModel):
    platform: Platform
    status: PostStatus = PostStatus.pending
    scheduled_at: datetime | None = None
    remote_id: str | None = None
    url: str | None = None
    error: str | None = None


class Clip(BaseModel):
    id: str  # e.g. "c01"
    start: float  # seconds in source
    end: float
    score: float = 0.0  # 0..1 highlight confidence
    reason: str = ""  # why analyze picked it
    # filled by render
    file: Path | None = None
    # filled by captions
    title: str | None = None
    caption: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    suggested_sound: str | None = None
    # filled by publish
    posts: list[Post] = Field(default_factory=list)

    @property
    def duration(self) -> float:
        return self.end - self.start


class Job(BaseModel):
    id: str
    source_url: str
    credit: str | None = None  # original creator / channel to credit
    title: str | None = None  # source video title
    status: JobStatus = JobStatus.created
    created_at: datetime = Field(default_factory=datetime.now)
    source_file: Path | None = None
    transcript_file: Path | None = None
    duration: float | None = None
    clips: list[Clip] = Field(default_factory=list)
    error: str | None = None

    # --- persistence helpers ---
    @staticmethod
    def dir_for(workspace: Path, job_id: str) -> Path:
        return workspace / "jobs" / job_id

    @classmethod
    def load(cls, workspace: Path, job_id: str) -> Job:
        path = cls.dir_for(workspace, job_id) / "manifest.json"
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, workspace: Path) -> Path:
        d = self.dir_for(workspace, self.id)
        d.mkdir(parents=True, exist_ok=True)
        path = d / "manifest.json"
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return path
