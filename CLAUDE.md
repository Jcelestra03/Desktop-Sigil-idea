# CLAUDE.md

Shared instructions for every agent working in this repo. Two people (Jcelestra03 and
Tiffany) work here, each with their own agent; the agents do not talk to each other, so
this file and `PLAN.md` are how you stay in sync.

## Read first

- `PLAN.md` — what we are building, who owns which files, the recognizer contract, and
  the branch/PR rules. Follow it. If a task would change the plan, say so instead of
  quietly doing something else.
- `LOG.md` — what has happened so far. Read the latest entries before starting.

## Project

Desktop Sigil: a Windows overlay where drawing a sigil with the mouse opens an app or
website. Python 3.11+, **standard library only** (tkinter, ctypes). Do not add
third-party dependencies without both teammates agreeing in `PLAN.md`.

Users never need the terminal: `Desktop Sigil.pyw` (double-click) opens the Sigil Book
window. Keep it that way — every user-facing feature belongs in the window, and the CLI
is for developers.

- `Desktop Sigil.pyw` — double-click launcher; shows a dialog + `sigil-error.log` on crash.
  Also the entry point of the .exe, which keeps data in `%APPDATA%\Desktop Sigil`.
- `build_exe.py`, `tools/make_icon.py`, `assets/sigil.ico` — the .exe build and its icon.
- `sigil/manager.py` — Sigil Book main window (an open grimoire drawn on one Canvas, with
  coordinate-based click areas instead of widgets), sigil editor dialog, floating ✦ button.
- `sigil/themes.py` — the four looks: Candlelight and Midnight (painted, `"art"` set) and
  Parchment and Obsidian (drawn). All dicts must have the same keys (a test checks this);
  read colors and fonts from the theme, never hard-code them.
- `sigil/artbook.py` — shows a painted look's picture (`assets/grimoire/`, made by
  `tools/render_art.py` with Edge) at the size that fits, and returns where its pages are.
- `sigil/grimoire.py` — draws the desk, props and pages. Seeded randomness, so redraws are
  stable. Items tagged `bg` (background), `front` (props above the writing), `fg` (page
  writing, redrawn on every click by `draw_pages`).
- `sigil/drawpad.py` — drawing canvas used in the editor, Paint-style pens (`PENS`,
  `render_stroke`), and thumbnail drawing. Pens only change looks; never the points.
- `sigil/tutorial.py` — the guided tour (drawn on the book canvas, tag `tour`), the
  optional practice cast, and `HELP`: the short text behind every "?" button.
- `sigil/recognizer.py` — $P point-cloud recognizer. Pure functions, no tkinter.
- `sigil/store.py` — loads/saves `sigils.json` and `settings.json` (gitignored, per-user).
- `sigil/actions.py` — runs a sigil's action; tidies typed targets (adds https://).
- `sigil/overlay.py` — full-screen tkinter drawing window.
- `sigil/hotkey.py` — Windows global hotkey via ctypes `RegisterHotKey`.
- `sigil/app.py` — `SigilApp`: wires hotkey → overlay → recognizer → action.
- `sigil/__main__.py` — CLI: `book` (default), `run`, `add`, `list`, `remove`, `test`.

## Commands

- Open the app: double-click `Desktop Sigil.pyw`, or `python -m sigil`
- Hotkey only, no window: `python -m sigil run`
- Tests: `python -m unittest`
- Build the .exe + zip for people without Python: `python build_exe.py` (needs
  `pip install pyinstaller`; build tool only, the app stays standard library only)
- Try things without touching your real sigils: set `SIGIL_FILE` to a temp path first.

## Rules for agents

1. Work on a branch named `<person>/<topic>`, never directly on `main`.
2. Stay inside the files your person owns (see the table in `PLAN.md`). If you need to
   change a file the other person owns, keep the change minimal and call it out in the PR.
3. Do not change the `recognize()` contract without updating `PLAN.md` in the same PR.
4. Run `python -m unittest` before proposing a commit.
5. Append a dated entry to `LOG.md` for every PR: what changed and why.
6. tkinter is not thread-safe: only touch widgets from the main thread. Other threads
   pass work through the queue in `app.py`.
7. Never commit `sigils.json` or `settings.json`.
8. Don't open the overlay while a dialog holds a grab (`SigilApp.summon` checks this);
   the overlay would get no mouse input.
