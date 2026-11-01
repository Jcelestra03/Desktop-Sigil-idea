"""Load and save the user's sigils in sigils.json.

Format:
    {
      "version": 1,
      "sigils": [
        {
          "name": "Canvas",
          "action": {"type": "url", "target": "https://canvas.uw.edu"},
          "templates": [ [ [[x, y], [x, y], ...], ... ], ... ]
        }
      ]
    }

Each template is one drawing (a list of strokes); a sigil keeps several samples.
Raw mouse points are stored, not normalized ones, so recognizer changes never
invalidate saved sigils.
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
            }
            for s in sigils
        ],
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)


def find(sigils: list[Sigil], name: str) -> Sigil | None:
    return next((s for s in sigils if s.name.lower() == name.lower()), None)
