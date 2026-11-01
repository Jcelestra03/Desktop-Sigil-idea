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
- `sigil/manager.py` — Sigil Book main window, sigil editor dialog, floating ✦ cast button.
- `sigil/drawpad.py` — drawing canvas used in the editor, and thumbnail drawing.
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
