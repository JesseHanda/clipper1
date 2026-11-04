# Clipper — CLAUDE.md

Two people build this repo by vibe-coding with Claude Code. Read this whole file before you change anything.

## What we're building
A tool that takes a YouTube link, cuts it into several vertical short clips (9:16, 15–60s), writes a caption and hashtags for each clip, and posts them to TikTok and Instagram Reels on a schedule. It targets GTA 6 gaming content, and **the deadline is the GTA 6 launch (Nov 19, 2026)**. Shipping beats polish. Only build what the pipeline needs.

## Pipeline (each stage is a separate module)
```
URL ─► ingest ─► analyze ─► render ─► captions ─► publish
       yt-dlp    find        ffmpeg     Claude API   TikTok / IG APIs
                 highlights  9:16 crop  caption +    + scheduler
                             subtitles  hashtags
```
Stages pass data **only through `workspace/jobs/<job_id>/manifest.json`**. That file follows the `Job` model in `clipper/models.py`. Each stage reads the manifest, does its work, fills in its own fields, updates `status`, and writes the manifest back. No stage imports another stage's internals.

```
workspace/jobs/<job_id>/
  manifest.json      # the Job model, the single source of truth
  source.mp4         # ingest
  transcript.json    # analyze
  clips/<clip_id>.mp4  # render
```

## Ownership (to avoid merge conflicts)
| Area | Owner | Folders |
|---|---|---|
| Engine: download, highlight detection, rendering | **Dev A** | `clipper/ingest`, `clipper/analyze`, `clipper/render` |
| Distribution: captions, posting, scheduling | **Dev B** | `clipper/captions`, `clipper/publish` |
| Shared contract | **both must agree** | `clipper/models.py`, `clipper/config.py`, `clipper/cli.py`, `pyproject.toml` |

- Stay inside your own folders. If you need a change in a shared file, keep it to a small PR of its own and tell the other person.
- **Changing `clipper/models.py` breaks the other person's work.** Only add optional fields. Never rename or remove a field without agreeing first. Update `tests/fixtures/sample_manifest.json` in the same PR.
- Dev B doesn't need to wait for Dev A. Build and test against `tests/fixtures/sample_manifest.json` and any short mp4.

## Git workflow
- `main` must always run. **Never commit directly to `main`.**
- Branch names: `a/<feature>` or `b/<feature>` (e.g. `a/highlight-detection`, `b/tiktok-upload`).
- One feature per branch, kept small. Open a PR and have the other person merge it.
- Before opening a PR, run `git pull origin main` (rebase or merge), then `uv run ruff check . && uv run pytest`.
- Commit messages use the imperative mood: "Add TikTok draft upload".
- Never commit `.env`, cookies, tokens, `workspace/` contents, or video/audio files. `.gitignore` covers these, so don't override it.

## Stack and commands
- Python 3.11+, managed with **uv**. FFmpeg must be on PATH.
- `uv sync`: install dependencies
- `uv run clipper run <youtube_url>`: run the full pipeline
- `uv run clipper <stage> <job_id>`: run one stage (`ingest|analyze|render|captions|publish`)
- `uv run pytest`: tests. `uv run ruff check . --fix && uv run ruff format .`: lint and format
- Libraries: `yt-dlp` (download), `faster-whisper` (transcription), `scenedetect` (scene cuts), `ffmpeg` via `subprocess` (all video work, no moviepy), `anthropic` (LLM), `httpx` (platform APIs), `typer` (CLI), `pydantic` (models).
- LLM: use the Anthropic SDK with the model from `config.py` (default `claude-sonnet-5-5`). Ask for JSON output and validate it with pydantic.

## Code conventions
- Type hints everywhere. Use `pathlib.Path`, never string paths, because the code must run on both Windows and macOS/Linux.
- Run ffmpeg with `subprocess.run([...], check=True)` and a list of arguments, never `shell=True`.
- Read every setting from `clipper/config.py`, which loads `.env`. No hardcoded keys, paths, or account names.
- Stages must be **re-runnable**. If an output file already exists, skip that work unless `--force` is passed.
- Use the `logging` module, not `print`, except for CLI output.
- Tests go in `tests/`. Use small fixtures. Don't download real videos in tests.

## Domain notes (read before working on analyze, render, or publish)
- **Gameplay highlights aren't mostly about speech.** Score candidate moments with audio loudness spikes (ffmpeg `ebur128`/`astats`), scene-cut density (`scenedetect`), and transcript reactions ("no way", laughter, shouting). Then send the top candidates and their transcript snippets to Claude to rank them and pick start and end times. Start each clip on the action. The first 1–2 seconds matter most.
- **Vertical format.** The default layout puts the gameplay scaled to fit the width over a blurred, zoomed copy of the same video in the background. Optionally, `facecam` mode puts the streamer's cam on top and gameplay below. Output is 1080x1920, H.264, AAC, 30fps.
- **Subtitles** are burned in from the whisper word timestamps: big, bold, centered, 2–4 words at a time.
- **Music: never burn copyrighted or "trending" songs into the file.** Platforms mute those videos or strike the account, and neither API lets you attach in-app sounds. We support two modes:
  - `MUSIC_MODE=in_app` (default): TikTok posts go to the **drafts/inbox**, and the human picks the trending sound in the app before publishing. The captions stage writes a `suggested_sound` from `trending_sounds.yaml`, which we update by hand each day.
  - `MUSIC_MODE=library`: mix a royalty-free track from `music/` under the gameplay audio at low volume.
- **TikTok Content Posting API:** an unaudited app can only post as `SELF_ONLY` (private). Default to the inbox/draft upload endpoint. Respect rate limits.
- **Instagram Graph API:** needs a Business or Creator account linked to a Facebook Page. Use the Reels container flow (create container → poll status → publish) with resumable upload.
- **Source content:** only process videos we're allowed to repost, such as our own gameplay or creators who said yes. Reposting other people's videos unchanged gets accounts flagged as "unoriginal." Keep the `source_url` and `credit` fields filled in.

## Definition of done for a PR
1. Ruff is clean and pytest passes.
2. The stage still works on the sample manifest.
3. The PR description says what changed and how to test it in about three lines.
