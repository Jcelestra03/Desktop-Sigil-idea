"""Run a sigil's action: open an app, file, folder, or URL."""

from __future__ import annotations

import os
import webbrowser


def describe(action: dict) -> str:
    return f"{action['type']}: {action['target']}"


def run(action: dict) -> None:
    kind, target = action["type"], action["target"]
    if kind == "url":
        webbrowser.open(target)
    elif kind in ("app", "file"):
        # ShellExecute: finds apps on PATH / App Paths, opens files with their default app
        os.startfile(target)
    else:
        raise ValueError(f"Unknown action type: {kind}")
