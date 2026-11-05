# Dev A plan: A1–A7 (engine)

Written Nov 5. Synced with `Realche3/clipper` at `9ffe635` (B1 llm + B2 captions merged).
Baseline: ruff clean, 25 tests pass. Applies the karpathy guidelines: least code that meets each
*Done when*, only Dev A folders, and a concrete check for every step.

## Assumptions (correct me if wrong)
1. **A local file counts as our own gameplay:** `credit=None`, `title` = file name. A URL gets
   `credit="@<uploader_id>"`, falling back to the channel name.
2. **Manifest paths are stored absolute.** `captions._resolve` already accepts both, and absolute
   works with any `WORKSPACE`.
3. **`analyze` is one stage, built up over A2→A4.** Until A4 lands it writes `transcript.json` but
   leaves `status=ingested`; A4 sets `analyzed`.
4. Real-URL and 20-minute benchmark runs happen on **your laptop**. The cloud container likely
   can't reach YouTube, and tests never use the network.

## 1. What we reuse (both repos are MIT; OpenShorts' `cloud/` folder is NOT, and we take nothing from it)

| From | What | Use | Why / where |
|---|---|---|---|
| OpenShorts `subtitles.py` `WHISPER_TRANSCRIBE_PARAMS` | `beam_size=5, vad_filter, condition_on_previous_text=False, word_timestamps` | **adapt** | A2. The `condition_on_previous_text=False` setting stops hallucinated repeats on noisy game audio. |
| OpenShorts `subtitles.merge_continuation_words` | glues word fragments that have no leading space back onto the previous word | **copy** | A2, so subtitles never show "YouTube -Kanal" style splits. |
| OpenShorts `subtitles._collect_word_blocks` | groups words into on-screen blocks by length and time | **adapt** | A6, limited to 2–4 words per block. |
| OpenShorts `subtitles.generate_ass` + `_ass_time`, `_escape_ass_text`, `hex_to_ass_color` | karaoke ASS: one event per word, active word recolored, no flicker in gaps | **adapt** | A6 core. Drop presets, effects, split-seam handling and the PlayResY=288 trick; use PlayRes 1080x1920. Keep their tested look: white bold text, black outline, yellow active word. |
| OpenShorts `ffmpeg_utils.cut_clip` | treats the output file (≥1 KB), not the exit code, as the verdict, and keeps ffmpeg's stderr | **idea** | A5 error handling. |
| OpenShorts `ffmpeg_utils.escape_filter_value` note | apostrophes in filter paths can't be escaped | **idea** | A6: the `.ass` file is always named `<clip_id>.ass` and run with `cwd=`, never named after a video title. |
| OpenShorts `ffmpeg_utils.blurred_backdrop` | blur at ¼ size, then scale up (~45% less CPU) | **idea, A7 only** | Use only if render misses its ≤3 min budget. |
| OpenShorts yt-dlp options | `noplaylist`; prefer `vcodec^=avc1` | **adapt** | A1. `ext=mp4` alone can return AV1, which decodes slowly on laptops (see Q2). |
| OpenShorts `speech_is_sparse` | under 8 words total or under 5 words/min counts as "no speech" | **idea** | A3/A4: treat speech as 0 instead of z-scoring noise, and tell Claude the clip has no speech. |
| OpenShorts clip-selection rule | "the LLM scores every window; the clip count is enforced in code" | **idea** | A4: Claude scores all ~15 candidates, and code picks the top N and fills any gap. |
| AutoClip `utils/download_recovery.py` | `cookiesfrombrowser=(browser,)`; when the browser's cookie database is locked (Chrome on Windows while it's open), retry once without cookies; detects "not a bot" errors | **adapt (small)** | A1: one retry without cookies, plus a clear error that says to close the browser or use `YTDLP_COOKIES_FROM_BROWSER`. |
| AutoClip yt-dlp options | `merge_output_format='mp4'`, `file_access_retries` (Windows file locks) | **copy options** | A1. |
| AutoClip `pipeline/clip_finder._dedupe` / `_parse` | drop picks that overlap a better one by more than 50% of the shorter clip; clamp score to 0..1; drop out-of-range picks | **adapt** | A4 validation of Claude's answer. |
| AutoClip research note (Oct 2026) | "where the clip starts" predicts views better than editing effects | **idea** | A7: tune the −8 s pre-roll so clips start on the action. |
| **Skipped** | AutoClip's whole outline → timeline → scoring LLM pipeline (transcript-only picking, rejected by D6); OpenShorts' face tracking (YOLO, mediapipe), reframe, GPU/NVENC, TransNetV2, Parakeet, Gemini vision, PIL hook PNGs, proxies | **skip** | Out of scope or stretch, or our design already covers it more simply (the hook goes in the same ASS file, so there is one burn). |

## 2. Per task

### A1 Ingest: `clipper/ingest/` (Nov 5)
- `__init__.py`: `run(job, force=False) -> Job`
- `download.py`:
  - `is_url(s: str) -> bool`
  - `ydl_options(dest: Path) -> dict`: spec format with an avc1 preference,
    `merge_output_format=mp4`, `noplaylist`, `file_access_retries`, `cookiesfrombrowser` when
    `config.YTDLP_COOKIES_FROM_BROWSER` is set.
  - `fetch(url, dest_dir) -> dict`: `extract_info(download=False)` first, so a source over
    `MAX_SOURCE_MINUTES` is rejected **before** downloading; then download. Retries once without
    browser cookies on a cookie-load error.
  - `metadata(info) -> dict`: title, description, channel, credit.
- `media.py`:
  - `probe_duration(path) -> float` (ffprobe)
  - `to_mp4(src, dst)`: copy if `.mp4`, else `ffmpeg -c copy` remux, because OBS records `.mkv`.
  - `extract_audio(src, wav)`: `-vn -ac 1 -ar 16000 pcm_s16le`.
- Writes `title, description, channel, credit, duration, source_file, audio_file` and
  `status=ingested`. Skips files that already exist unless `--force`. Duration always comes from
  ffprobe.
- Tests (`tests/test_ingest.py`): a 5 s `testsrc`+`sine` video made with ffmpeg in `tmp_path`.
  - A local file gives `ingested`, about 5 s, and a 16 kHz mono wav (checked with `wave`).
  - A cap of 0.01 min raises a clear error.
  - A re-run doesn't re-copy.
  - A mocked `yt_dlp.YoutubeDL` checks the options, the metadata mapping and the early length
    reject.
- **Done check:** `uv run clipper run <tmp.mp4> --until ingest` gives `status=ingested`. Then
  you run one real YouTube URL on your laptop.

### A2 Transcribe: `clipper/analyze/transcribe.py` (Nov 6)
- `transcribe(audio: Path, model_name: str) -> Transcript`: faster-whisper, int8, `device="auto"`,
  with OpenShorts' params and `merge_continuation_words`.
- `analyze.run` writes `transcript.json` and sets `transcript_file`. It skips if the file exists,
  unless `--force`.
- Tests: a fake `WhisperModel` returning canned segments checks the conversion to `Transcript`,
  the fragment merge and the skip-if-exists. No model download in tests.
- **Done check:** on your laptop, a 2-minute clip gives a valid `transcript.json`, and the time
  taken is logged.

### A3 Signals + candidates: `analyze/signals.py`, `analyze/candidates.py` (Nov 7–8)
Pure numpy functions, except `detect_cuts`.
- `signals.py`:
  - `loudness_per_second(samples, sr) -> ndarray` (RMS in dB)
  - `zscore(x)`: returns zeros when std is 0
  - `detect_cuts(video) -> list[float]`: PySceneDetect `ContentDetector` at 360p
  - `cut_density(cuts, n, window=5)`
  - `speech_per_second(transcript, n)`: words/s plus reaction-keyword hits
  - `combine(loud, cuts, speech) -> ndarray`: `0.5/0.3/0.2` weights, then a 3 s moving average.
    Speech counts as 0 when it's sparse.
- `candidates.py`:
  - `Candidate(start, end, peak, score, stats)`
  - `pick_peaks(score, k, min_gap=20)`
  - `pauses(transcript) -> list[float]`
  - `make_window(peak, pauses, duration)`: −8 s / +20 s, snapped to the nearest pause, clamped
    to `[CLIP_MIN, CLIP_MAX]` and to the source length.
  - `find_candidates(...)`
- The wav is read with stdlib `wave` and `numpy.frombuffer`, so there's no new audio library.
- Tests on synthetic arrays:
  - peaks are ≥20 s apart, and the top k come out in order
  - a flat signal gives no NaNs
  - windows snap to a pause and respect min/max and the source edges
  - the cut density window and keyword hits count correctly
- **Done check:** the unit tests pass, and on a real job the top 15 candidates are logged with
  their stats.

### A4 Ranker: `analyze/rank.py` (Nov 9)
- Schema: `RankedClip(index, start, end, score, reason)`, `Ranking(clips)`. Called through
  `llm.ask_json` only.
- Prompt inputs:
  - `context`, `title`, `description`
  - per candidate: index, window, peak loudness z, cuts in the window, words/s, and the
    transcript snippet (or "no speech")
  - the instruction: **score every candidate** and refine start/end inside its window
- Code then:
  - validates each pick: a real index, inside its window, a valid duration
  - clamps the score to 0..1
  - drops picks that overlap a better one by more than 50%
  - takes the top `CLIPS_PER_VIDEO`
  - fills any shortfall from the signal ranking
- On `LLMError`, it falls back to the top N candidates by signal score.
- Clip ids `c01…` follow start time. Sets `status=analyzed`.
- Tests: `ask_json` is monkeypatched to return a good answer, a bad one (out-of-window,
  duplicates, too few picks) and an `LLMError`. Each case must give exactly N valid clips.
- **Done check:** `clipper run <file> --until analyze` gives `status=analyzed` with N clips,
  and `clipper stage captions` works on it.

### A5 Render: `clipper/render/` (Nov 10)
- `layout.py`: `filter_graph(ass_name: str | None) -> str`. It's the ARCHITECTURE blur graph,
  plus `subtitles=<clip_id>.ass` after the overlay, on the 1080x1920 canvas.
- `encode.py`:
  - `ffmpeg_args(source, start, end, ass_name, out_name) -> list[str]`: `-ss/-to` before `-i`,
    `loudnorm=I=-14:TP=-1.5`, `libx264 veryfast crf20 r30 yuv420p`, `aac 128k`,
    `+faststart`.
  - `render_clip(...)`: runs ffmpeg with `cwd=clips_dir` and `check=True`. The output must
    exist and be ≥1 KB; otherwise it raises with the tail of stderr.
- `run(job, force=False, clip_id: str | None = None)`: sets `clip.file` and `status=rendered`.
- **Shared change:** `--clip` on `clipper stage`, passed through `_run_stage` (a few lines in
  `cli.py`). Dev B needs to know.
- Tests:
  - the argument list is pure
  - one real 3 s render of `testsrc` where ffprobe shows 1080x1920 at 30 fps with audio
- **Done check:** a rendered clip plays correctly on your laptop.

### A6 Subtitles + hook: `render/subtitles.py` (Nov 11)
- `group_words(words, clip_start, clip_end, min_words=2, max_words=4, max_gap=0.8) -> list[list[Word]]`
- `build_ass(blocks, hook_text: str | None) -> str`:
  - captions: bold white text with a black outline and a yellow active word, alignment 2,
    margin about 500 px (the lower third)
  - hook: larger text at alignment 8 (the top third) from 0–3 s
  - text is escaped
- `write_ass(clip, transcript, path)`. Render passes the relative name `<clip_id>.ass`.
- Tests (pure):
  - the 2–4 word grouping
  - clip-relative times
  - one event per word with no gaps inside a block
  - the hook event spans 0–3 s
  - `{}\` are escaped
  - no words gives a hook only, and no hook either gives an empty file, so render skips the
    filter
- **Done check:** on the sample manifest plus `testsrc`, the burned subtitles and hook show in a
  frame grab.

### A7 Tuning (Nov 13–16)
- Each stage logs how long it took. Run one 20-minute 1080p video on your laptop and compare
  against the §9 budget.
- Fixes, in this order:
  1. `WHISPER_MODEL=base`
  2. CUDA if the laptop has an Nvidia GPU
  3. the ¼-size blur
- Quality: review 5 jobs' clips and tune the pre-roll and the `0.5/0.3/0.2` weights. These are
  module constants, not new settings.

## 3. Order
Nov 5 A1 → Nov 6 A2 → Nov 7–8 A3 → Nov 9 A4 → Nov 10 A5 → Nov 11 A6 → **Nov 12 M1** → Nov 13–16 A7
→ Nov 17 freeze. Each task is one `a/<feature>` branch, merged into clipper1 `main`, then a
`ship/<feature>` branch for you to move upstream.

## 4. Risks and open questions
1. **YouTube download risk:** recent yt-dlp versions need a JavaScript runtime (deno) for many
   YouTube formats, and bot checks happen. Mitigation: keep yt-dlp updated, use
   `YTDLP_COOKIES_FROM_BROWSER`, and local-file input as a fallback. Please install deno on the
   laptop if the first real download fails.
2. **Q1:** Is a local file always our own gameplay (credit None)? If not, I'll take
   `--context`-style credit input later. No change now.
3. **Q2 (shared, ARCHITECTURE §5.1):** add an `[vcodec^=avc1]` preference to the format string.
   It's a one-line doc edit that needs Dev B's 👍.
4. **Q3 (shared, `pyproject.toml`):** declare `numpy` explicitly. It's only a transitive
   dependency today, through faster-whisper and opencv.
5. **Shared `cli.py --clip`** (A5) needs Dev B told. It's small and only adds things.
6. The whisper `small` model is about 460 MB and downloads on first run. Do it once on the
   laptop before launch day.
7. Fonts: Arial (bold) via libass/fontconfig. It exists on Windows and macOS; the Linux CI
   falls back to whatever font is installed, which is fine for tests.
