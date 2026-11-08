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

1. **Double-click `Desktop Sigil.pyw`.** The *Sigil Book* opens: an open grimoire with
   your *Sigil Index* on the left page. A small ✦ button appears near the bottom-right of
   your screen. Switch between the **Parchment** and **Obsidian** grimoire at the top.
2. Click **✒ Inscribe a new sigil** on the right page:
   - Give it a name.
   - Choose what it opens: a **Program**, **Website**, **File** or **Folder**.
   - Click **Browse…** to pick the program (an `.exe`, or a shortcut from your desktop
     or Start menu), or type the web address.
   - Pick a pen (**Pen, Brush, Calligraphy, Quill, Marker, Spray, Glow**), a size and an
     ink color in the toolbar above the drawing pad (✦ is the grimoire's own ink; **More…**
     picks any color). **↶ Undo** (or Ctrl+Z) removes the last stroke.
   - Draw the sigil on the pad and click **Add this drawing**. Do this 3 times, drawing it
     the same way each time. The pen is only for looks: it never changes how the sigil is
     recognized.
   - Click **Save sigil**.
3. **Cast it:** click the floating ✦ button, **✦ Cast a sigil** in the window, or press
   **Ctrl+Alt+S**. Draw the sigil and let go; after a moment it opens.

| In the drawing screen | |
| --- | --- |
| Draw | Hold the left mouse button. Several strokes are fine. |
| Cast | Stop drawing for a moment, or press **Enter** |
| Cancel | **Esc** or right-click |

Keep the Sigil Book open (minimizing is fine) for the ✦ button and the hotkey to work.

### Sharing sigils

Select a sigil and click **Share**. You can **Save .sigil file…** and send the file, or
**Copy code** and paste the code (it starts with `SIGIL1-`) into Discord, a text or an
email. One code always fits in one Discord message.

To add one someone sent you, click **✉ Receive a sigil**, then open their `.sigil` file or
paste their code (a copied code is filled in for you, and it still works if the chat app
split it over several lines).

- **Their paths become yours.** Folders that differ between computers are sent as
  placeholders (`%LOCALAPPDATA%\Discord\Update.exe`), so it points to your copy. Steam and
  other programs are also looked for in the other Program Files folder. If it's still not
  found, click **Browse…** and pick your copy.
- **Nothing runs when you receive a sigil.** You see what it opens first. Scripts
  (`.bat`, `.ps1`…), programs outside the usual install folders, and links that open other
  programs get a warning, and you have to tick *I trust who sent this* to add them.
- **Add your own drawing.** The drawings are the sender's, so the sigil may not always
  recognize the way you draw it. Leave *Add my own drawing after this* ticked and the
  editor opens so you can add one.
- Already have a sigil with that name? It's added as "Canvas (2)", or tick *Replace*.

### More

- **Test a drawing** shows which sigil a drawing matches without opening anything.
- Click a sigil in the index to show its seal on the right page, with **Edit**, **Test it**
  and **Erase**. Editing changes what it opens or adds/removes drawings (click a drawing
  to remove it). Double-clicking a sigil in the index also opens it for editing.
- More sigils than fit on the page? **turn page ▸** / **◂ turn back**, or the mouse wheel.
- **The ✦ button:** drag it anywhere; right-click it for a menu. Turn it on or off with
  *Floating ✦ button* at the bottom of the right page.
- **Hotkey:** click **Hotkey: … · change** at the bottom of the right page to pick another
  shortcut, for example if another program already uses Ctrl+Alt+S.
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

Jcelestra03 and Tifanie, TCSS 490 Fall 2026. See `PLAN.md` for the plan and `LOG.md`
for what's changed.
