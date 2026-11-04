# Clipper

YouTube link → vertical clips with captions → TikTok + Instagram Reels. The target is the GTA 6 launch on **Nov 19, 2026**.
Read [CLAUDE.md](CLAUDE.md) first. Claude Code loads it automatically.

## Setup (both devs)
1. Install Python 3.11+, [uv](https://docs.astral.sh/uv/), and FFmpeg.
   On Windows: `winget install Python.Python.3.12 astral-sh.uv Gyan.FFmpeg`
2. `uv sync`
3. `cp .env.example .env` and fill in your keys.
4. `uv run pytest`

## Do these today (approval takes days)
- [ ] **TikTok:** create an app at developers.tiktok.com, add *Content Posting API*, and **submit it for audit now**. Until it's audited, posts can only be private, so we use draft/inbox upload for now.
- [ ] **Instagram:** switch the IG account to Creator/Business, link it to a Facebook Page, and create a Meta app with `instagram_content_publish`. You can test your own account in dev mode.
- [ ] Get an Anthropic API key.

## Task split
Use one branch per task and open a PR into `main`. Dev B starts by testing against `tests/fixtures/sample_manifest.json`.

| # | Dev A: Engine | Dev B: Distribution |
|---|---|---|
| 1 | `ingest`: yt-dlp download (≤1080p mp4) plus title and channel into the manifest | `captions`: Claude writes the title, caption, and hashtags, plus `suggested_sound` from `trending_sounds.yaml` |
| 2 | `analyze`: faster-whisper transcript with word timestamps | `publish/tiktok.py`: OAuth plus **inbox/draft** video upload |
| 3 | `analyze`: candidate scoring (loudness + scene cuts + reactions), then Claude picks the clips | `publish/instagram.py`: Reels container → poll → publish |
| 4 | `render`: 9:16 blur layout, burned-in word subtitles | `publish/scheduler.py`: spaces posts `POST_INTERVAL_MINUTES` apart, retries, never double-posts |
| 5 | `render`: facecam layout, optional royalty-free music mix | Simple status view (CLI table, or a small web page if there's time) |
| 6 | **Together:** full end-to-end run on a real video, then tune clip quality | |

Every stage module exposes `run(job: Job, force: bool = False) -> Job` in its `__init__.py`.
