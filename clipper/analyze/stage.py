"""Analyze stage: transcript -> (A3 signals + candidates) -> (A4 Claude ranker).

Spec: docs/ARCHITECTURE.md §5.2. Until the ranker lands, this only writes transcript.json
and leaves status at `ingested`.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from clipper import config
from clipper.analyze.transcribe import transcribe
from clipper.models import Job

log = logging.getLogger(__name__)


def run(job: Job, force: bool = False) -> Job:
    if job.audio_file is None or not Path(job.audio_file).exists():
        raise RuntimeError("audio.wav is missing; run the ingest stage first")

    job_dir = Job.dir_for(config.WORKSPACE, job.id).resolve()
    job_dir.mkdir(parents=True, exist_ok=True)
    path = job_dir / "transcript.json"
    if force or not path.exists():
        transcript = transcribe(Path(job.audio_file), config.WHISPER_MODEL)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(transcript.model_dump_json(indent=2), encoding="utf-8")
        os.replace(tmp, path)
    else:
        log.info("transcript.json exists; skipping transcription (use --force to redo)")
    job.transcript_file = path
    return job
