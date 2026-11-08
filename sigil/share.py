"""Share sigils between people: as a .sigil file or as a short text code.

Both carry the same thing: the sigil's name, what it opens, its drawings and its pen
style. Pure Python, no tkinter, so it can be tested anywhere.

Three things make sharing safe and useful:

1. Paths are made portable. C:\\Users\\jem\\AppData\\Local\\Discord\\Update.exe is sent as
   %LOCALAPPDATA%\\Discord\\Update.exe and turned back into the receiver's own path. If the
   target still isn't there, the Sigil Book asks the receiver to find their copy.
2. Nothing runs on import. `review()` lists anything worth a second look (scripts,
   programs outside the usual install folders, links that open other programs) so the
   receiver can decide before the sigil is added.
3. The drawings are the sender's. The Sigil Book suggests adding your own drawing too,
   so the sigil recognizes the way *you* draw it.

A text code looks like SIGIL1-eNpz... : zlib-compressed and URL-safe base64, so it
survives being pasted into Discord, email or a text message. Spaces and line breaks
inside a code are ignored, and the code is found even inside a longer message.
"""

from __future__ import annotations

import base64
import json
import ntpath
import os
import re
import zlib
from dataclasses import dataclass, field
from typing import Callable, Mapping

from .recognizer import Stroke
from .store import Sigil

FILE_EXT = ".sigil"
CODE_PREFIX = "SIGIL1-"
FORMAT = "desktop-sigil"
VERSION = 1

SHORT_CODE_CHARS = 1000      # aim for this while the drawings stay crisp
MAX_CODE_CHARS = 1800        # always fits in one Discord message (2000)
MAX_FILE_BYTES = 2_000_000
MAX_NAME = 60
MAX_TEMPLATES = 12
MAX_STROKES = 60
MAX_POINTS = 6000            # per drawing
MAX_COORD = 20000

KINDS = ("app", "url", "file", "folder")
PENS = ("pen", "brush", "calligraphy", "quill", "marker", "spray", "glow")

# Windows folders that differ between computers, most specific first.
PLACES = ("LOCALAPPDATA", "APPDATA", "USERPROFILE", "ProgramFiles(x86)", "ProgramFiles",
          "ProgramData", "SystemRoot")

# Files that run code when opened.
SCRIPTS = {".bat", ".cmd", ".ps1", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh", ".hta",
           ".scr", ".pif", ".com", ".reg", ".msi", ".jar"}
PROGRAMS = SCRIPTS | {".exe"}


class ShareError(ValueError):
    """The file or code isn't a sigil, or is damaged. The message is for the user."""


@dataclass
class Received:
    """A sigil that arrived from someone else, before it's added to the book."""
    name: str
    kind: str
    shared_target: str            # as it was sent, with %PLACEHOLDERS%
    target: str                   # turned into a path on this computer
    templates: list[list[Stroke]]
    style: dict = field(default_factory=dict)

    def to_sigil(self, name: str | None = None, target: str | None = None) -> Sigil:
        return Sigil(name or self.name, {"type": self.kind, "target": target or self.target},
                     self.templates, dict(self.style))


# ---- portable paths ------------------------------------------------------------

def _env(env: Mapping[str, str] | None) -> dict[str, str]:
    """Environment variables, matched case-insensitively like Windows does."""
    return {k.upper(): v for k, v in (os.environ if env is None else env).items()}


def portable_target(kind: str, target: str, env: Mapping[str, str] | None = None) -> str:
    """C:\\Users\\jem\\AppData\\Local\\x -> %LOCALAPPDATA%\\x, for app/file/folder paths."""
    if kind == "url" or not ntpath.isabs(target):
        return target
    values = _env(env)
    norm = ntpath.normcase(ntpath.normpath(target))
    best = None
    for name in PLACES:
        value = values.get(name.upper())
        if not value:
            continue
        base = ntpath.normcase(ntpath.normpath(value))
        if norm == base or norm.startswith(base.rstrip("\\") + "\\"):
            if best is None or len(base) > len(best[1]):
                best = (name, base)
    if best is None:
        return target
    rest = ntpath.normpath(target)[len(best[1]):]
    return f"%{best[0]}%{rest}"


def local_target(kind: str, target: str, env: Mapping[str, str] | None = None) -> str:
    """%LOCALAPPDATA%\\x -> this computer's path. Unknown %NAMES% are left as they are."""
    if kind == "url":
        return target
    values = _env(env)
    return re.sub(r"%([^%\\/]+)%", lambda m: values.get(m.group(1).upper(), m.group(0)), target)


def unresolved(target: str) -> bool:
    """True if a %PLACE% couldn't be filled in on this computer."""
    return bool(re.search(r"%[^%\\/]+%", target))


def find_target(kind: str, shared: str, env: Mapping[str, str] | None = None,
                exists: Callable[[str], bool] = os.path.exists) -> tuple[str, bool]:
    """Where the target is on this computer, and whether it was found there.

    Programs installed as 32-bit on one PC and 64-bit on another live in different
    Program Files folders, so both are tried."""
    target = local_target(kind, shared, env)
    if kind != "url" and unresolved(target):
        return target, False
    if kind == "url" or not ntpath.isabs(target):
        return target, True  # websites and bare names like notepad.exe can't be checked
    if exists(target):
        return target, True
    for a, b in (("%ProgramFiles%", "%ProgramFiles(x86)%"),
                 ("%ProgramFiles(x86)%", "%ProgramFiles%")):
        if shared.lower().startswith(a.lower()):
            other = local_target(kind, b + shared[len(a):], env)
            if exists(other):
                return other, True
    return target, False


# ---- safety review ----------------------------------------------------------------

def review(kind: str, target: str, env: Mapping[str, str] | None = None) -> list[str]:
    """Plain-language notes about anything a receiver should think twice about.
    An empty list means nothing unusual. Never blocks anything by itself."""
    notes = []
    if kind == "url":
        scheme = target.split(":", 1)[0].lower() if ":" in target else ""
        if scheme not in ("http", "https"):
            notes.append(f"This link starts with “{scheme}:”, so it opens another program "
                         "instead of a web page (for example steam: opens Steam). Only add it "
                         "if you expected that.")
        return notes

    ext = ntpath.splitext(target)[1].lower()
    if ext in SCRIPTS:
        notes.append(f"This runs a {ext} script. Scripts can change or delete things on your "
                     "computer. Only add it if you trust who sent it and know what it does.")
    elif kind == "file" and ext in PROGRAMS:
        notes.append("This “file” is actually a program. Only add it if you trust who sent it.")
    elif kind == "app" and ntpath.isabs(target) and not _usual_place(target, env):
        notes.append("This program isn't in a usual install folder (like Program Files). "
                     "Programs sent along with a sigil could be harmful. Only add it if you "
                     "trust who sent it.")
    return notes


def _usual_place(path: str, env: Mapping[str, str] | None) -> bool:
    values = _env(env)
    norm = ntpath.normcase(ntpath.normpath(path))
    places = [values.get("PROGRAMFILES"), values.get("PROGRAMFILES(X86)"),
              values.get("SYSTEMROOT")]
    if values.get("LOCALAPPDATA"):
        local = values["LOCALAPPDATA"]
        # per-user installs: Discord, Spotify, VS Code, Squirrel apps...
        places.append(local)
    for root in (values.get("APPDATA"), values.get("PROGRAMDATA")):
        if root:
            places.append(ntpath.join(root, "Microsoft", "Windows", "Start Menu"))
    temp = values.get("TEMP")
    if temp and norm.startswith(ntpath.normcase(ntpath.normpath(temp)) + "\\"):
        return False
    return any(p and norm.startswith(ntpath.normcase(ntpath.normpath(p)).rstrip("\\") + "\\")
               for p in places)


def sender_notes(sigil: Sigil, env: Mapping[str, str] | None = None) -> list[str]:
    """Things the sender should know about how the sigil will work on someone else's PC."""
    kind, target = sigil.action["type"], sigil.action["target"]
    if kind == "url":
        return []
    shared = portable_target(kind, target, env)
    if shared.upper().startswith("%USERPROFILE%"):
        what = {"folder": "folder", "file": "file"}.get(kind, "program")
        return [f"This {what} is in your own user folder, so it only works for someone "
                f"who has the same {what} in the same place. They'll be asked to find "
                "their copy if it's missing."]
    if ntpath.isabs(target) and shared == target:
        return ["This path is specific to your computer. If they keep it somewhere else, "
                "they'll be asked to find their copy."]
    return []


# ---- payload ---------------------------------------------------------------------

def _payload(sigil: Sigil, env: Mapping[str, str] | None) -> dict:
    kind = sigil.action["type"]
    return {
        "format": FORMAT,
        "version": VERSION,
        "name": sigil.name,
        "action": {"type": kind, "target": portable_target(kind, sigil.action["target"], env)},
        "style": {k: v for k, v in sigil.style.items() if k in ("pen", "size", "color")},
    }


def _check(data: object, templates: object) -> Received:
    """Validate everything that came from outside; raise ShareError if anything's off."""
    try:
        assert isinstance(data, dict)
        name = data["name"]
        action = data["action"]
        kind, target = action["type"], action["target"]
        style = data.get("style") or {}
        assert isinstance(name, str) and isinstance(target, str) and isinstance(style, dict)
    except (AssertionError, KeyError, TypeError):
        raise ShareError("This isn't a sigil, or part of it is missing.") from None
    if data.get("version", VERSION) > VERSION:
        raise ShareError("This sigil was made by a newer Desktop Sigil. Update yours first.")
    name = " ".join(name.split())[:MAX_NAME]
    if not name:
        raise ShareError("This sigil has no name.")
    if kind not in KINDS:
        raise ShareError("This sigil opens something Desktop Sigil doesn't know about.")
    if not target.strip() or len(target) > 2000 or "\0" in target:
        raise ShareError("This sigil doesn't say what it opens.")

    clean_style = {}
    if style.get("pen") in PENS:
        clean_style["pen"] = style["pen"]
    if isinstance(style.get("size"), (int, float)) and 1 <= style["size"] <= 30:
        clean_style["size"] = int(style["size"])
    color = style.get("color")
    if color is None or (isinstance(color, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", color)):
        clean_style["color"] = color

    clean = []
    try:
        assert isinstance(templates, list) and 0 < len(templates) <= MAX_TEMPLATES
        for t in templates:
            assert isinstance(t, list) and 0 < len(t) <= MAX_STROKES
            drawing = []
            for stroke in t:
                pts = [(float(x), float(y)) for x, y in stroke]
                assert all(abs(x) <= MAX_COORD and abs(y) <= MAX_COORD for x, y in pts)
                if len(pts) > 1:
                    drawing.append(pts)
            assert drawing and sum(len(s) for s in drawing) <= MAX_POINTS
            clean.append(drawing)
    except (AssertionError, TypeError, ValueError):
        raise ShareError("This sigil's drawings are damaged.") from None

    return Received(name, kind, target, local_target(kind, target), clean, clean_style)


# ---- .sigil files ------------------------------------------------------------------

def to_file_text(sigil: Sigil, env: Mapping[str, str] | None = None) -> str:
    data = _payload(sigil, env)
    data["templates"] = [[[[round(x, 1), round(y, 1)] for x, y in s] for s in t]
                         for t in sigil.templates]
    return json.dumps(data, ensure_ascii=False)


def from_file_text(text: str) -> Received:
    if len(text) > MAX_FILE_BYTES:
        raise ShareError("This file is too big to be a sigil.")
    try:
        data = json.loads(text)
    except ValueError:
        raise ShareError("This file isn't a sigil.") from None
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise ShareError("This file isn't a Desktop Sigil sigil.")
    return _check(data, data.get("templates"))


def save_file(sigil: Sigil, path: str, env: Mapping[str, str] | None = None) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(to_file_text(sigil, env))


def load_file(path: str) -> Received:
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            raise ShareError("This file is too big to be a sigil.")
        with open(path, encoding="utf-8") as f:
            return from_file_text(f.read())
    except UnicodeDecodeError:
        raise ShareError("This file isn't a sigil.") from None
    except OSError as e:
        raise ShareError(f"Couldn't open the file: {e.strerror or e}") from None


# ---- text codes ---------------------------------------------------------------------
# The drawings are packed as small whole-number steps (most fit in one byte), then the
# whole thing is compressed. If a code is still too long for one chat message, the
# drawings are simplified a little at a time (fewer points along straight-ish parts)
# until it fits; recognition only looks at the overall shape, so it still works.

def _zigzag(n: int) -> int:
    return n * 2 if n >= 0 else -n * 2 - 1


def _unzigzag(n: int) -> int:
    return n // 2 if n % 2 == 0 else -(n + 1) // 2


def _put(out: bytearray, n: int) -> None:
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)


def _pack(templates: list[list[Stroke]]) -> bytes:
    out = bytearray()
    _put(out, len(templates))
    for t in templates:
        _put(out, len(t))
        for stroke in t:
            _put(out, len(stroke))
            px = py = 0
            for x, y in stroke:
                ix, iy = round(x), round(y)
                _put(out, _zigzag(ix - px))
                _put(out, _zigzag(iy - py))
                px, py = ix, iy
    return bytes(out)


def _unpack(data: bytes) -> list[list[Stroke]]:
    pos = 0

    def get() -> int:
        nonlocal pos
        n = shift = 0
        while True:
            if pos >= len(data) or shift > 35:
                raise ShareError("This sigil code is damaged.")
            b = data[pos]
            pos += 1
            n |= (b & 0x7F) << shift
            shift += 7
            if b < 0x80:
                return n

    templates = []
    for _ in range(min(get(), MAX_TEMPLATES + 1)):
        drawing = []
        for _ in range(min(get(), MAX_STROKES + 1)):
            stroke, x, y = [], 0, 0
            for _ in range(min(get(), MAX_POINTS + 1)):
                x += _unzigzag(get())
                y += _unzigzag(get())
                stroke.append((float(x), float(y)))
            drawing.append(stroke)
        templates.append(drawing)
    return templates


def _simplify(stroke: Stroke, tolerance: float) -> Stroke:
    """Ramer–Douglas–Peucker: drop points that are within `tolerance` px of the line."""
    if tolerance <= 0 or len(stroke) < 3:
        return list(stroke)
    keep = [False] * len(stroke)
    keep[0] = keep[-1] = True
    todo = [(0, len(stroke) - 1)]
    while todo:
        a, b = todo.pop()
        (ax, ay), (bx, by) = stroke[a], stroke[b]
        dx, dy = bx - ax, by - ay
        length = (dx * dx + dy * dy) ** 0.5
        far, far_i = -1.0, -1
        for i in range(a + 1, b):
            px, py = stroke[i]
            d = (abs(dy * px - dx * py + bx * ay - by * ax) / length if length
                 else ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5)
            if d > far:
                far, far_i = d, i
        if far > tolerance:
            keep[far_i] = True
            todo += [(a, far_i), (far_i, b)]
    return [p for p, k in zip(stroke, keep) if k]


def _encode(data: dict, templates: list[list[Stroke]]) -> str:
    raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode() + b"\0" + \
        _pack(templates)
    body = base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode().rstrip("=")
    return CODE_PREFIX + body


def to_code(sigil: Sigil, env: Mapping[str, str] | None = None) -> str:
    data = _payload(sigil, env)
    n = len(sigil.templates)
    # (drawings kept, simplification in px, longest acceptable code), gentlest first:
    # sub-pixel simplification is invisible; past that, send three drawings rather than
    # blur them all; only very busy drawings get simplified harder.
    tries = [(n, 1.0, SHORT_CODE_CHARS), (n, 1.5, SHORT_CODE_CHARS), (n, 2.5, MAX_CODE_CHARS),
             (min(n, 3), 2.5, MAX_CODE_CHARS), (min(n, 3), 4, MAX_CODE_CHARS),
             (min(n, 2), 6, MAX_CODE_CHARS), (1, 9, MAX_CODE_CHARS)]
    code = ""
    for keep, tolerance, limit in tries:
        templates = [[_simplify(s, tolerance) for s in t] for t in sigil.templates[:keep]]
        code = _encode(data, templates)
        if len(code) <= limit:
            return code
    return code


def find_code(text: str) -> str | None:
    """The first sigil code in a pasted message, with any line breaks taken out."""
    joined = re.sub(r"\s+", "", text)
    m = re.search(re.escape(CODE_PREFIX) + r"[A-Za-z0-9_\-]+", joined)
    return m.group(0) if m else None


def from_code(text: str) -> Received:
    code = find_code(text)
    if code is None:
        raise ShareError(f"That isn't a sigil code. Codes start with {CODE_PREFIX}")
    body = code[len(CODE_PREFIX):]
    try:
        packed = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        z = zlib.decompressobj()
        raw = z.decompress(packed, MAX_FILE_BYTES)
        if z.unconsumed_tail:
            raise ShareError("This sigil code is too big.")
        if not z.eof:
            raise ShareError("This sigil code is cut off. Ask for it again and copy all of it.")
    except (ValueError, zlib.error):
        raise ShareError("This sigil code is damaged or cut off. Ask for it again and copy "
                         "all of it.") from None
    head, sep, strokes = raw.partition(b"\0")
    try:
        data = json.loads(head.decode())
    except (UnicodeDecodeError, ValueError):
        raise ShareError("This sigil code is damaged.") from None
    if not sep:
        raise ShareError("This sigil code is damaged.")
    return _check(data, _unpack(strokes))


# ---- name clashes ---------------------------------------------------------------------

def free_name(name: str, taken: list[str]) -> str:
    """'Canvas' -> 'Canvas (2)' if the book already has a Canvas."""
    lower = {t.lower() for t in taken}
    if name.lower() not in lower:
        return name
    n = 2
    while f"{name} ({n})".lower() in lower:
        n += 1
    return f"{name} ({n})"
