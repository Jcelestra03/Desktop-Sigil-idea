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

- `sigil/recognizer.py` — $P point-cloud recognizer. Pure functions, no tkinter.
- `sigil/store.py` — loads/saves `sigils.json` (gitignored, per-user).
- `sigil/actions.py` — runs a sigil's action.
- `sigil/overlay.py` — full-screen tkinter drawing window.
- `sigil/hotkey.py` — Windows global hotkey via ctypes `RegisterHotKey`.
- `sigil/app.py` — wires hotkey → overlay → recognizer → action.
- `sigil/__main__.py` — CLI: `run`, `add`, `list`, `remove`, `test`.

## Commands

- Run: `python -m sigil run`
- Teach a sigil: `python -m sigil add "Name" --app "C:\path\to\app.exe"` or `--url https://...`
- Tests: `python -m unittest`

## Rules for agents

1. Work on a branch named `<person>/<topic>`, never directly on `main`.
2. Stay inside the files your person owns (see the table in `PLAN.md`). If you need to
   change a file the other person owns, keep the change minimal and call it out in the PR.
3. Do not change the `recognize()` contract without updating `PLAN.md` in the same PR.
4. Run `python -m unittest` before proposing a commit.
5. Append a dated entry to `LOG.md` for every PR: what changed and why.
6. tkinter is not thread-safe: only touch widgets from the main thread. Other threads
   pass work through the queue in `app.py`.
7. Never commit `sigils.json`.
