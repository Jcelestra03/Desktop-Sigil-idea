# Desktop Sigil — Team Plan

TCSS 490, Artifact 4 ("For Someone Else"). Due **Sunday, November 8, 2026, 11:59 PM**.

This is the single plan both of us (and both of our agents) work from. If the plan
changes, change it here in a pull request and add an entry to `LOG.md`.

## What we are building

A Windows desktop overlay inspired by *Witch Hat Atelier*: press a hotkey, the
screen dims, you draw a sigil with the mouse, and the sigil "casts" — it opens
an app, file, folder, or website.

- **Summon:** global hotkey `Ctrl+Alt+S` (configurable) opens a full-screen translucent overlay.
- **Draw:** one or more strokes. When you stop drawing for a moment (or press Enter)
  the drawing is recognized. `Esc` or right-click cancels.
- **Cast:** the best-matching sigil's action runs (`os.startfile` for apps/files/folders,
  `webbrowser.open` for URLs). If nothing matches well enough, the overlay says so.
- **Teach:** `python -m sigil add <name> --app <path>` or `--url <url>` asks you to
  draw the new sigil three times and saves it.

Recognition uses the **$P point-cloud recognizer** (Vatavu, Anthony & Wobbrock, 2012):
it handles multi-stroke drawings and does not care about stroke order or direction,
which suits sigils. No machine learning, no training data beyond the user's own drawings.

Python standard library only (tkinter + ctypes), so there is nothing to install.

## Who it is for

**TODO (both):** name the real person we are building for, someone not on our team.

- Person: _______________
- What they open every day (apps / sites / folders): _______________
- What they said they want from it: _______________
- Date we interviewed them: _______________
- Date we handed it over: _______________

Their answers decide which sigils we preload, which hotkey we use, and what we
polish in week 2.

## Who owns what

| Area | Owner | Files |
| --- | --- | --- |
| Overlay window, drawing, visual feel | Jcelestra03 | `sigil/overlay.py` |
| Global hotkey + main run loop | Jcelestra03 | `sigil/hotkey.py`, `sigil/app.py` |
| Recognizer | Tiffany | `sigil/recognizer.py`, `tests/test_recognizer.py` |
| Sigil storage + teaching flow (`add`, `list`, `remove`) | Tiffany | `sigil/store.py`, `sigil/__main__.py` |
| Actions (launching apps / URLs) | shared | `sigil/actions.py` |
| Docs, plan, log | shared | `*.md` |

"Owner" means you review and merge changes to that area; anyone may propose a change.

### The contract between the halves

The overlay hands the recognizer a list of strokes; the recognizer never touches tkinter,
and the overlay never does geometry.

```python
Point  = tuple[float, float]
Stroke = list[Point]

recognizer.recognize(strokes: list[Stroke], sigils: list[Sigil]) -> Match | None
# Match has .sigil and .score (0..1, higher is better)
```

Changing this signature needs both of us to agree, in a PR.

## How we avoid colliding

1. `main` always runs. Nobody commits directly to `main` after the initial setup commit.
2. One branch per task: `<name>/<short-topic>`, e.g. `tiffany/recognizer-threshold`,
   `jcelestra/overlay-glow`.
3. Open a pull request; the **other** person reviews and merges it.
4. Before opening a PR: `python -m unittest` passes, and add a line to `LOG.md`.
5. Pull `main` before starting a new branch. Keep PRs small (one idea each).
6. `sigils.json` (your personal sigils) is gitignored — don't commit it.

## Milestones

| When | Goal |
| --- | --- |
| Sun Nov 1 | Repo set up, prototype runs end to end, portfolio check-in card submitted |
| Tue Nov 3 | Interview our person; fill in "Who it is for"; list their sigils |
| Thu Nov 5 | Features from the interview done (see backlog) |
| Sat Nov 7 | Hand it over: install it on their machine / demo it, collect feedback |
| Sun Nov 8 | Final log entries, portfolio cards, Canvas submissions |

## Backlog (pick from here, in order of what our person cares about)

- [ ] Preload sigils for our person's apps and sites
- [ ] Settings window to add/remove sigils without the command line
- [ ] Start with Windows (shortcut in the Startup folder) + tray icon
- [ ] Multi-monitor overlay (currently primary monitor only)
- [ ] Nicer "casting" animation (glow, fade, rune circle)
- [ ] Tune the match threshold with real drawings from our person
- [x] Configurable hotkey (`--hotkey`, `SIGIL_HOTKEY`)
