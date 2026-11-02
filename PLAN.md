# Desktop Sigil — Team Plan

TCSS 490, Artifact 4 ("For Someone Else"). Due **Sunday, November 8, 2026, 11:59 PM**.

This is the single plan both of us (and both of our agents) work from. If the plan
changes, change it here in a pull request and add an entry to `LOG.md`.

## What we are building

A Windows desktop overlay inspired by *Witch Hat Atelier*: press a hotkey, the
screen dims, you draw a sigil with the mouse, and the sigil "casts" — it opens
an app, file, folder, or website.

- **No terminal needed:** double-click `Desktop Sigil.pyw` to open the *Sigil Book*
  window, which lists your sigils and lets you add, edit, delete and test them.
- **Teach:** *New sigil* → name it, pick Program / Website / File / Folder (Browse… for
  an `.exe` or shortcut, or type a web address), draw it 3 times on the pad, save.
- **Summon:** click the floating ✦ button, the *Cast a sigil* button, or press the
  hotkey `Ctrl+Alt+S` (changeable in the window). A full-screen translucent overlay opens.
- **Draw:** one or more strokes. When you stop drawing for a moment (or press Enter)
  the drawing is recognized. `Esc` or right-click cancels.
- **Cast:** the best-matching sigil's action runs (`os.startfile` for apps/files/folders,
  `webbrowser.open` for URLs). If nothing matches well enough, the overlay says so.
- The command line (`python -m sigil add/list/remove/test/run`) still works for developers.

Recognition uses the **$P point-cloud recognizer** (Vatavu, Anthony & Wobbrock, 2012):
it handles multi-stroke drawings and does not care about stroke order or direction,
which suits sigils. No machine learning, no training data beyond the user's own drawings.

Python standard library only (tkinter + ctypes), so there is nothing to install.

### Where it stands

There was a **mock build**: it worked end to end (Sigil Book window, sigil editor,
floating ✦ button, overlay, recognizer), but we decided to **change the look and theme of
the window** to make it more attractive before handing it to Jun.

The window is now drawn as an **open grimoire**, in two versions you can switch between at
the top of the window (the choice is remembered):

- **Parchment**: aged pages with faint rune writing and stains, red-ink seals, gilt edges,
  on white fur with an amethyst sphere, crystal ball, twigs, beads and a red ribbon.
- **Obsidian**: black pages with gold ink, a bone-bead strand down the spine and a quill,
  on teal wood with black candles, seal coins and parchment scraps.

Left page: the *Sigil Index* (turn pages with ◂ ▸ or the mouse wheel). Right page: the
selected sigil's seal and the actions. Next: decide with Tiffany which version (or both)
Jun gets by default.

## Ideas we considered first

Before settling on sigils, we thought about:

- **Invoice orders** for Jcelestra03's sister and the company she works for.
- **A mini music player for several people**, a better version of Spotify Jam.
- **A desktop app to resize Windows' UI and taskbar.**

We picked the sigil overlay because it's made for a specific friend (Jun) and connects
to things they already love.

## Who it is for

**Jun**, a friend of ours who loves playing games, likes drawing art, and loves the anime
*Witch Hat Atelier*, the anime this whole idea comes from. Drawing a sigil to open a game
brings together all three things Jun enjoys.

Jun doesn't know we're making this for them yet; it's a surprise. We're confident they'll
love it, but because it's a surprise we have to work out what they need without asking
them directly.

- What they open every day (apps / sites / folders): _______________
- What we learned about what they'd want: _______________
- Date we handed it over: _______________

What we learn about Jun decides which sigils we preload (likely their games and drawing
apps), which hotkey we use, and what we polish in week 2.

## Who owns what

| Area | Owner | Files |
| --- | --- | --- |
| Overlay window, drawing, visual feel | Jcelestra03 | `sigil/overlay.py`, `sigil/drawpad.py` |
| Sigil Book window, editor, floating ✦ button, launcher | Jcelestra03 | `sigil/manager.py`, `Desktop Sigil.pyw` |
| Grimoire look: the two themes and the book drawing | Jcelestra03 | `sigil/themes.py`, `sigil/grimoire.py` |
| Global hotkey + main run loop | Jcelestra03 | `sigil/hotkey.py`, `sigil/app.py` |
| Recognizer | Tiffany | `sigil/recognizer.py`, `tests/test_recognizer.py` |
| Sigil + settings storage, command line | Tiffany | `sigil/store.py`, `sigil/__main__.py` |
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
6. `sigils.json` and `settings.json` (your personal sigils and settings) are gitignored —
   don't commit them.

## Milestones

| When | Goal |
| --- | --- |
| Sun Nov 1 | Repo set up, prototype runs end to end, portfolio check-in card submitted |
| Tue Nov 3 | Find out which games and apps Jun uses (without spoiling the surprise); list their sigils |
| Thu Nov 5 | New look and theme for the window done; Jun's sigils preloaded |
| Sat Nov 7 | Surprise Jun: install it on their machine, show them, collect feedback |
| Sun Nov 8 | Final log entries, portfolio cards, Canvas submissions |

## Backlog (pick from here, in order of what Jun cares about)

- [x] Redesign the look and theme of the Sigil Book window so it's more attractive
  (open grimoire, Parchment and Obsidian versions)
- [x] Bigger sigil editor with Paint-style pens, sizes and colors (saved with each sigil)
- [ ] Pick Jun's default grimoire; theme the drawing overlay to match (red / gold ink)
- [ ] Preload sigils for Jun's games and apps
- [x] Settings window to add/remove sigils without the command line (Sigil Book)
- [x] A way to cast without the hotkey (floating ✦ button)
- [ ] Start with Windows (shortcut in the Startup folder) + tray icon
- [ ] Multi-monitor overlay (currently primary monitor only)
- [ ] Nicer "casting" animation (glow, fade, rune circle)
- [ ] Tune the match threshold with real drawings (ours, then Jun's)
- [x] Configurable hotkey (`--hotkey`, `SIGIL_HOTKEY`)
