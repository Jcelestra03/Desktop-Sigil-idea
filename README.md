# Desktop Sigil

Draw a sigil on your desktop to open an app or website, like the wizards in
*Witch Hat Atelier* drawing spells.

Click the floating ✦ button (or press **Ctrl+Alt+S**), the screen dims, draw your sigil
with the mouse, and it casts: Steam opens, or Canvas, or your notes folder.

## Requirements

- Windows 10 or 11
- Python 3.11 or newer from [python.org](https://www.python.org/downloads/) (tkinter is
  included). No other packages.

## Getting started

1. **Double-click `Desktop Sigil.pyw`.** The *Sigil Book* window opens, and a small ✦
   button appears near the bottom-right of your screen.
2. Click **+ New sigil**:
   - Give it a name.
   - Choose what it opens: a **Program**, **Website**, **File** or **Folder**.
   - Click **Browse…** to pick the program (an `.exe`, or a shortcut from your desktop
     or Start menu), or type the web address.
   - Draw the sigil on the pad and click **Add this drawing**. Do this 3 times, drawing it
     the same way each time.
   - Click **Save sigil**.
3. **Cast it:** click the floating ✦ button, **✦ Cast a sigil** in the window, or press
   **Ctrl+Alt+S**. Draw the sigil and let go; after a moment it opens.

| In the drawing screen | |
| --- | --- |
| Draw | Hold the left mouse button. Several strokes are fine. |
| Cast | Stop drawing for a moment, or press **Enter** |
| Cancel | **Esc** or right-click |

Keep the Sigil Book open (minimizing is fine) for the ✦ button and the hotkey to work.

### More

- **Test a drawing** shows which sigil a drawing matches without opening anything.
- **Edit** a sigil to change what it opens, or to add or remove drawings (click a drawing
  to remove it). Double-clicking a sigil also opens it for editing.
- **The ✦ button:** drag it anywhere; right-click it for a menu. Turn it off with the
  *Floating cast button* checkbox.
- **Hotkey:** click **Change** at the bottom of the window to pick another shortcut,
  for example if another program already uses Ctrl+Alt+S.
- Your sigils are saved in `sigils.json` and settings in `settings.json`, next to this
  README (set `SIGIL_FILE` to keep them somewhere else). Neither is committed to git.

## For developers: command line

Everything in the window can also be done from a terminal:

```bash
python -m sigil                                   # open the Sigil Book (same as double-click)
python -m sigil run                               # hotkey only, no window
python -m sigil add "Canvas" --url https://canvas.uw.edu
python -m sigil add "Notepad" --app notepad.exe
python -m sigil list
python -m sigil remove "Canvas"
python -m sigil test
python -m unittest                                # run the tests
```

## How recognition works

Each drawing is turned into a cloud of 32 evenly spaced points, scaled and centered, and
compared to every saved drawing with the
[$P point-cloud recognizer](https://depts.washington.edu/acelab/proj/dollar/pdollar.html).
Because it compares point clouds, stroke order and direction don't matter.

## Team

Jcelestra03 and Tiffany, TCSS 490 Fall 2026. See `PLAN.md` for the plan and `LOG.md`
for what's changed.
