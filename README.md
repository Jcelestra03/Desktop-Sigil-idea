# Desktop Sigil

Draw a sigil on your desktop to open an app or website, like the wizards in
*Witch Hat Atelier* drawing spells.

Press **Ctrl+Alt+S**, the screen dims, draw your sigil with the mouse, and it casts:
Steam opens, or Canvas, or your notes folder.

## Requirements

- Windows 10 or 11
- Python 3.11 or newer (from python.org; tkinter is included). No other packages.

## Quick start

```bash
# 1. Teach it some sigils. You'll draw each one 3 times.
python -m sigil add "Canvas" --url https://canvas.uw.edu
python -m sigil add "Notepad" --app notepad.exe

# 2. Start listening for the hotkey
python -m sigil run
```

Then press **Ctrl+Alt+S** and draw.

If another program already uses that shortcut, pick a different one:

```bash
python -m sigil run --hotkey ctrl+alt+q
```

(or set the `SIGIL_HOTKEY` environment variable). Modifiers: ctrl, alt, shift, win.
Keys: a–z, 0–9, space, f1–f12.

| While drawing | |
| --- | --- |
| Draw | Hold left mouse button. Several strokes are fine. |
| Cast | Stop drawing for a moment, or press **Enter** |
| Cancel | **Esc** or right-click |

## Other commands

```bash
python -m sigil list            # show your sigils
python -m sigil remove "Canvas" # forget a sigil
python -m sigil test            # draw once and see what it matches, without launching
```

`add` also accepts `--file` for any file or folder, and `--samples N` to draw it more or
fewer times. Running `add` with an existing name adds more samples to that sigil, which
helps if it isn't recognized reliably.

Your sigils are saved in `sigils.json` next to this README (set `SIGIL_FILE` to keep them
somewhere else).

## How recognition works

Each drawing is turned into a cloud of 32 evenly spaced points, scaled and centered, and
compared to every saved sample with the
[$P point-cloud recognizer](https://depts.washington.edu/acelab/proj/dollar/pdollar.html).
Because it compares point clouds, stroke order and direction don't matter.

## Team

Jcelestra03 and Tiffany, TCSS 490 Fall 2026. See `PLAN.md` for the plan and `LOG.md`
for what's changed.
