"""Suggested trending sounds from the hand-maintained trending_sounds.yaml."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

log = logging.getLogger(__name__)


class Sound(BaseModel):
    name: str
    platform: str = "tiktok"
    vibe: str = "hype"


def load_sounds(path: Path) -> list[Sound]:
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return [Sound.model_validate(s) for s in data.get("sounds") or []]
    except (yaml.YAMLError, ValidationError, AttributeError) as e:
        log.warning("could not read %s (%s); no sound suggestions", path, e)
        return []


def pick_sound(sounds: list[Sound], vibe: str | None, index: int = 0) -> str | None:
    """Pick a sound matching the vibe; rotate by `index` so clips don't all get the same one."""
    if not sounds:
        return None
    matches = [s for s in sounds if s.vibe == vibe] or sounds
    return matches[index % len(matches)].name
