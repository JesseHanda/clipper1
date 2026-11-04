"""All settings come from .env (see .env.example). Never hardcode secrets."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default)


WORKSPACE = Path(_get("WORKSPACE", str(ROOT / "workspace")))
MUSIC_DIR = ROOT / "music"
TRENDING_SOUNDS_FILE = ROOT / "trending_sounds.yaml"

# LLM
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = _get("CLAUDE_MODEL", "claude-sonnet-5-5")

# Clipping
CLIPS_PER_VIDEO = int(_get("CLIPS_PER_VIDEO", "5"))
CLIP_MIN_SECONDS = float(_get("CLIP_MIN_SECONDS", "15"))
CLIP_MAX_SECONDS = float(_get("CLIP_MAX_SECONDS", "60"))
WHISPER_MODEL = _get("WHISPER_MODEL", "small")
LAYOUT = _get("LAYOUT", "blur")  # blur | facecam
MUSIC_MODE = _get("MUSIC_MODE", "in_app")  # in_app | library

# TikTok
TIKTOK_CLIENT_KEY = _get("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = _get("TIKTOK_CLIENT_SECRET")
TIKTOK_ACCESS_TOKEN = _get("TIKTOK_ACCESS_TOKEN")

# Instagram (Graph API)
IG_USER_ID = _get("IG_USER_ID")
IG_ACCESS_TOKEN = _get("IG_ACCESS_TOKEN")

# Scheduling
POST_INTERVAL_MINUTES = int(_get("POST_INTERVAL_MINUTES", "90"))
