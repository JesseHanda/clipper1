"""All settings come from .env (see .env.example). Never hardcode secrets."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _bool(name: str, default: bool) -> bool:
    return _get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


WORKSPACE = Path(_get("WORKSPACE", str(ROOT / "workspace")))
DB_FILE = WORKSPACE / "clipper.db"
SECRETS_DIR = ROOT / "secrets"
MUSIC_DIR = ROOT / "music"
TRENDING_SOUNDS_FILE = ROOT / "trending_sounds.yaml"

# Safety
DRY_RUN = _bool("DRY_RUN", True)  # True = never touch real accounts
AUTO_APPROVE = _bool("AUTO_APPROVE", False)

# LLM
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = _get("CLAUDE_MODEL", "claude-opus-5-5")
CLAUDE_EFFORT = _get("CLAUDE_EFFORT", "medium")  # low | medium | high | xhigh | max

# Ingest
MAX_SOURCE_MINUTES = int(_get("MAX_SOURCE_MINUTES", "90"))
YTDLP_COOKIES_FROM_BROWSER = _get("YTDLP_COOKIES_FROM_BROWSER")  # e.g. "chrome"

# Analyze / clipping
CLIPS_PER_VIDEO = int(_get("CLIPS_PER_VIDEO", "5"))
CANDIDATES = int(_get("CANDIDATES", "15"))
CLIP_MIN_SECONDS = float(_get("CLIP_MIN_SECONDS", "15"))
CLIP_MAX_SECONDS = float(_get("CLIP_MAX_SECONDS", "60"))
WHISPER_MODEL = _get("WHISPER_MODEL", "small")

# Render
LAYOUT = _get("LAYOUT", "blur")  # blur | facecam (stretch)
MUSIC_MODE = _get("MUSIC_MODE", "in_app")  # in_app | library (stretch)

# Captions
BASE_HASHTAGS = _get("BASE_HASHTAGS", "#gta6 #gta #gaming").split()

# Publish
TIKTOK_CLIENT_KEY = _get("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = _get("TIKTOK_CLIENT_SECRET")
IG_APP_ID = _get("IG_APP_ID")
IG_APP_SECRET = _get("IG_APP_SECRET")
ENABLED_PLATFORMS = _get("ENABLED_PLATFORMS", "tiktok,instagram").split(",")
POST_INTERVAL_MINUTES = int(_get("POST_INTERVAL_MINUTES", "90"))
POSTING_WINDOW = _get("POSTING_WINDOW", "10:00-23:30")  # local time
DAILY_CAP_TIKTOK = int(_get("DAILY_CAP_TIKTOK", "6"))
DAILY_CAP_INSTAGRAM = int(_get("DAILY_CAP_INSTAGRAM", "5"))
