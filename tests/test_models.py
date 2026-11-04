from pathlib import Path

from clipper.models import Job, Transcript

FIXTURES = Path(__file__).parent / "fixtures"


def test_sample_manifest_matches_contract():
    job = Job.model_validate_json((FIXTURES / "sample_manifest.json").read_text(encoding="utf-8"))
    assert job.clips and job.clips[0].duration > 0


def test_sample_transcript_matches_contract():
    t = Transcript.model_validate_json(
        (FIXTURES / "sample_transcript.json").read_text(encoding="utf-8")
    )
    assert "NO WAY" in t.text_between(42.5, 71.0)


def test_roundtrip(tmp_path):
    job = Job(id="t1", source_url="https://youtu.be/x")
    job.save(tmp_path)
    assert Job.load(tmp_path, "t1").source_url == job.source_url
