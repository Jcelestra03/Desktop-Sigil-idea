"""Run a sigil's action: open an app, file, folder, or URL."""

from __future__ import annotations

import os
import webbrowser

KINDS = {
    "app": "Program",
    "url": "Website",
    "file": "File",
    "folder": "Folder",
}


def describe(action: dict) -> str:
    return f"{action['type']}: {action['target']}"


def normalize_target(kind: str, target: str) -> str:
    """Tidy what the user typed: add https:// to bare web addresses, clean up paths."""
    target = target.strip().strip('"')
    if kind == "url":
        if target and "://" not in target:
            target = "https://" + target
        return target
    if os.sep in target or "/" in target:
        return os.path.normpath(target)
    return target  # bare program names like notepad.exe are found on PATH


def run(action: dict) -> None:
    kind, target = action["type"], action["target"]
    if kind == "url":
        webbrowser.open(target)
    elif kind in ("app", "file", "folder"):
        # ShellExecute: finds apps on PATH / App Paths, opens files with their default app
        os.startfile(target)
    else:
        raise ValueError(f"Unknown action type: {kind}")
