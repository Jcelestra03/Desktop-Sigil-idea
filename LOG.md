# Log

Newest entries at the bottom. One entry per PR or decision: date, who, what, why.
Agents append here too (see `CLAUDE.md`).

---

## 2026-11-01 — Project setup (Jcelestra03, with Claude)

**Planned**
- Idea: a desktop overlay where drawing a sigil (as in *Witch Hat Atelier*) opens an
  app or website.
- Wrote `PLAN.md`: ownership split (Jcelestra03 owns overlay/hotkey/run loop; Tiffany owns
  recognizer/storage/teaching flow), branch + PR rules, milestones, backlog.
- Wrote shared `CLAUDE.md` so both agents work from the same plan.

**Built**
- Working prototype, standard library only:
  - `$P` point-cloud recognizer (multi-stroke, order/direction independent).
  - Full-screen translucent overlay; recognizes after a short pause or on Enter.
  - Global hotkey `Ctrl+Alt+S` via Win32 `RegisterHotKey`, changeable with `--hotkey`.
  - CLI: `run`, `add`, `list`, `remove`, `test`.
  - Unit tests for the recognizer and store.

**Decisions**
- Chose `$P` over `$1`: sigils are often multi-stroke and people won't always draw strokes
  in the same order.
- No third-party packages so nobody has to fight installs, and handover to our person
  is just "install Python, run this".
- Each user's sigils live in `sigils.json` (gitignored), not in the repo.
- Planned `Ctrl+Alt+Space` as the hotkey, but another program on Jcelestra03's PC already
  owns it, so the default is `Ctrl+Alt+S` and `--hotkey` / `SIGIL_HOTKEY` override it.
  Lesson for handover: check the hotkey is free on our person's machine.
- Match threshold set to 0.45 from synthetic tests (same shape ≥ ~0.53, different ≤ ~0.40).
  Needs tuning with real drawings.

**Verified**
- `python -m unittest`: 10 tests pass.
- End-to-end on Windows 11: hotkey registers, overlay opens full-screen, a drawn circle
  was recognized (score 0.82) and its action ran, overlay closed.
- Not yet tried by a person drawing by hand.

**Next**
- Interview the person we're building for and fill in "Who it is for" in `PLAN.md`.
- Tiffany: review the setup PR / first commit.

---

## 2026-11-01 — Sigil Book window: no terminal needed (Jcelestra03, with Claude, `jem-branch`)

**Why**
- Jcelestra03 wanted the person we hand this to never to type terminal commands or
  depend mainly on a hotkey, and to assign sigils to an `.exe` or a website from a window.

**Changed**
- New `Desktop Sigil.pyw`: double-click to open the app (no console window).
- New *Sigil Book* window (`sigil/manager.py`): list of sigils with drawing thumbnails;
  New / Edit / Delete; *Cast a sigil* and *Test a drawing* buttons; status line.
- Sigil editor dialog: name, Program / Website / File / Folder, Browse… for `.exe` or
  shortcuts (or type a web address), drawing pad (`sigil/drawpad.py`) to draw it 3 times,
  click a drawing to remove it. Warns about missing fields, too few drawings, drawings
  that differ a lot, or a sigil that looks like an existing one.
- Floating ✦ cast button: always on top, click to cast, drag to move, right-click menu.
- Hotkey can be changed from the window; settings (hotkey, button on/off and position) are
  saved in `settings.json` (gitignored).
- `SigilApp` reworked so the window and the headless `run` command share it.
- `python -m sigil` with no command now opens the window.

**Touched Tiffany's files** (please review): `store.py` gained `load_settings` /
`save_settings`; `__main__.py` gained the `book` command as the default.

**Bug found while testing**
- If the editor was open, clicking ✦ or pressing the hotkey opened an overlay that
  couldn't be drawn on (the editor held the mouse grab). Casting now waits until the
  dialog is closed.

**Verified**
- `python -m unittest`: 17 tests pass (new: web-address cleanup, hotkey parsing, settings).
- Scripted run of the real window on Windows 11: created "YouTube" in the editor
  (`youtube.com` saved as `https://youtube.com`), clicked ✦, drew the star, and it cast
  YouTube (99% match). Screenshots checked.
- Not yet tried by hand by a person; the actual browser/app launch was stubbed out in the
  scripted run.

---

## 2026-11-01 — Who it's for, where it stands, earlier ideas (Jcelestra03, with Claude, `jem-branch`)

**Decided**
- We're building this for **Jun**, a friend who loves games, drawing art, and
  *Witch Hat Atelier*. It's a surprise: Jun doesn't know yet, so we'll learn which games
  and apps they use without asking directly.
- The current build is a mock build. We want to change the look and theme of the window
  to make it more attractive before handover. Added to the backlog and the Nov 5 milestone.
- Recorded the ideas we considered before this one: invoice orders for Jcelestra03's
  sister's company, a multi-person mini music player (a better Spotify Jam), and a desktop
  app to resize Windows' UI and taskbar.

**Changed**
- `PLAN.md`: filled in "Who it is for", added "Where it stands" and "Ideas we considered
  first", reworded milestones and backlog around Jun and the surprise handover.

---

## 2026-11-02 — The window becomes an open grimoire, in two versions (Jcelestra03, with Claude, `jem-branch`)

**Why**
- The mock build worked but looked plain. Jcelestra03 shared two reference pictures of
  open grimoires and asked for one version based on each.

**Changed**
- The Sigil Book is now drawn on one canvas as an open book on a desk (`sigil/grimoire.py`):
  left page is the *Sigil Index* (each sigil in an ink seal ring, ◂ ▸ to turn pages, mouse
  wheel works too); right page shows the selected sigil as a large rune seal with Edit /
  Test it / Erase, plus Inscribe / Cast / Test actions, hotkey and ✦-button settings.
- Two themes (`sigil/themes.py`), switchable at the top of the window and saved in
  `settings.json`:
  - **Parchment** (picture 1): aged pages, faint rune writing, stains, red-ink seals,
    gilt page edges; white fur desk, amethyst sphere, crystal ball, twigs, beads, ribbon.
  - **Obsidian** (picture 2): black pages, gold ink, bone-bead strand on the spine,
    quill; teal wood desk, black candles, seal coins, parchment scraps.
- Sigil editor and floating ✦ button follow the chosen theme; the drawing pad uses the
  theme's ink (red or gold).
- Fonts are all built into Windows (Gabriola, Palatino Linotype, Segoe UI Historic /
  Symbol), so it looks the same on Jun's PC.

**Verified**
- `python -m unittest`: 20 tests pass (new: theme color blend, both themes have the same
  keys, unknown theme falls back to Parchment).
- Screenshots of both themes (book, welcome page, editor) checked. Full redraw ~80 ms,
  redraw on a click ~15 ms.
- Simulated clicks: selecting a sigil, turning the page, switching theme (and it's saved).
- Not yet: someone using it by hand; the drawing overlay itself is still the old purple/gold
  look (backlog).

---

## 2026-11-02 — Bigger sigil editor with Paint-style pens (Jcelestra03, with Claude, `jem-branch`)

**Why**
- The *Inscribe a new sigil* window was too small to draw on comfortably, and Jcelestra03
  wanted different pen types, sizes and colors like MS Paint.

**Changed**
- Drawing pad grows with the screen: 640 px on a 1080p screen (was 300 px), smaller
  screens get at least 380 px. Saved drawings moved to the left column (88 px previews),
  and the editor opens centered on the book.
- Toolbar above the pad: 7 pens (Pen, Brush with tapered ends, Calligraphy with a 45°
  flat nib, Quill that thins when you move fast and pools ink at the ends, Marker, Spray,
  Glow), a size slider (1–30) with a live preview, 12 color swatches (the first is the
  grimoire's own ink, so it follows Parchment/Obsidian) plus **More…** for any color,
  and **↶ Undo** / Ctrl+Z.
- Changing the pen restyles the whole drawing. The style is saved with the sigil and
  used for its seal in the index and on the right page.
- `store.py` (Tiffany's): optional `style` field on each sigil. Older `sigils.json`
  files load unchanged. Recognition never reads it.

**Verified**
- `python -m unittest`: 24 tests pass (new: every pen draws, styled thumbnails,
  undo/restyle never change the points, style saved and old files still load).
- Screenshots of the editor (brush, quill) and the book with four differently-styled
  sigils, in both grimoires.
- Not yet: drawing by hand with a real mouse, and the cast overlay still uses its own
  single pen.
