"""Load and save the user's sigils in sigils.json.

Format:
    {
      "version": 1,
      "sigils": [
        {
          "name": "Canvas",
          "action": {"type": "url", "target": "https://canvas.uw.edu"},
          "templates": [ [ [[x, y], [x, y], ...], ... ], ... ],
          "style": {"pen": "brush", "size": 8, "color": "#a32a1e"}   (optional)
        }
      ]
    }

Each template is one drawing (a list of strokes); a sigil keeps several samples.
Raw mouse points are stored, not normalized ones, so recognizer changes never
invalidate saved sigils. "style" is only how the sigil looks (pen, size, color; color
null means the grimoire's ink); recognition never uses it.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .recognizer import Stroke

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "sigils.json"


def sigil_path() -> Path:
    return Path(os.environ.get("SIGIL_FILE", DEFAULT_PATH))


@dataclass
class Sigil:
    name: str
    action: dict
    templates: list[list[Stroke]] = field(default_factory=list)
    style: dict = field(default_factory=dict)


def load(path: Path | None = None) -> list[Sigil]:
    path = path or sigil_path()
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        Sigil(
            name=s["name"],
            action=s["action"],
            templates=[[[(x, y) for x, y in stroke] for stroke in t] for t in s["templates"]],
            style=s.get("style", {}),
        )
        for s in data.get("sigils", [])
    ]


def save(sigils: list[Sigil], path: Path | None = None) -> None:
    path = path or sigil_path()
    data = {
        "version": 1,
        "sigils": [
            {
                "name": s.name,
                "action": s.action,
                "templates": [
                    [[[round(x, 1), round(y, 1)] for x, y in stroke] for stroke in t]
                    for t in s.templates
                ],
                **({"style": s.style} if s.style else {}),
            }
            for s in sigils
        ],
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)


def find(sigils: list[Sigil], name: str) -> Sigil | None:
    return next((s for s in sigils if s.name.lower() == name.lower()), None)


# App settings (hotkey, floating button) live beside sigils.json in settings.json.
SETTINGS_DEFAULTS = {"hotkey": "ctrl+alt+s", "orb": True, "orb_pos": None, "theme": "parchment"}


def settings_path() -> Path:
    return sigil_path().with_name("settings.json")


def load_settings(path: Path | None = None) -> dict:
    path = path or settings_path()
    settings = dict(SETTINGS_DEFAULTS)
    if path.exists():
        settings.update(json.loads(path.read_text(encoding="utf-8")))
    return settings


def save_settings(settings: dict, path: Path | None = None) -> None:
    (path or settings_path()).write_text(json.dumps(settings, indent=2), encoding="utf-8")
