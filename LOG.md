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

---

## 2026-11-08 — Even text layout in the Sigil Book (pixelgaming457 (Tifanie Ngo), with Claude, in 'tifanie-branch')

**Why**
- Text on the pages didn't look even, especially after resizing: positions were fixed
  pixel offsets, so on small windows the Edit / Test it / Erase row ran into the actions,
  on big windows everything bunched at the top, and with Windows display scaling (125 %,
  150 %) the bigger fonts overlapped the dividers.

**Changed**
- `manager.py`: text is placed by its baseline and spaced in ems (font size in pixels),
  so gaps stay even at any size, scaling and font. Type grows a little on big windows and
  shrinks on small ones so the right page always fits.
- Both pages share one grid: the title and ✦ divider sit at the same height on both
  pages (the right page's title is the selected sigil's name, or "Desktop Sigil"), and
  the last lines (folio / status) share a baseline.
- Right page: the seal and its details are centered in the space above the actions, and
  the seal grows with the window. The three actions are centered as a block; the hotkey
  and floating-button switches are centered and go on two lines when the page is narrow.
- Index rows: seal and text are centered in each row; row height follows the font.
- "Grimoire: Parchment Obsidian" is centered over the spine.
- `grimoire.py`: runes on the Obsidian paper scraps skip the area behind the switch.

**Verified**
- `python -m unittest`: 24 tests pass.
- Screenshots at 1000×680, 1160×760 and 1600×1000, both grimoires, empty / selected /
  several folios, and at 150 % scaling. Simulated clicks: select, turn page, switch theme,
  long status, wrapped hotkey line.

---

## 2026-11-08 — Share sigils with friends (pixelgaming457 (Tifanie Ngo), with Claude, in 'tifanie-branch')

**Why**
- Tifanie wanted people to send each other sigils and use them on their own PC, as a
  file or as a short text code.

**Changed**
- New `sigil/share.py` (no tkinter): `.sigil` files (JSON) and `SIGIL1-` text codes
  (drawings packed as small steps, zlib, URL-safe base64; simplified only as much as needed
  to stay under 1,000 characters when possible and always under 1,800, so a code fits one
  Discord message). Codes are found inside a longer message and survive line breaks.
- Paths are portable: `%LOCALAPPDATA%`, `%APPDATA%`, `%USERPROFILE%`, Program Files etc.
  are swapped in when sending and filled in on the receiver's PC; both Program Files
  folders are tried. Unknown placeholders count as not found.
- Safety: everything from outside is validated (types, sizes, pens, colors, a cap on
  decompressed size). Nothing runs on import. `review()` flags scripts, programs outside
  usual install folders or in Temp, `.exe` "files", and non-http links; the receiver must
  tick *I trust who sent this* to add those.
- New `sigil/share_dialogs.py`: **Share** button next to Edit / Test it / Erase (save file
  or copy code); **✉ Receive a sigil** on the right page (open file or paste code, shows
  the seal, what it opens and whether it's found, Browse… to relink, name clash → "Name
  (2)" or Replace, and *Add my own drawing after this* opens the editor).
- `manager.py`: the Share button, the Receive action, the right page now lays out four
  action lines.

**Verified**
- `python -m unittest`: 40 tests pass (new `tests/test_share.py`: portable paths, both
  Program Files, unknown places, review notes, code and file round trips, codes inside chat
  messages, very busy drawings still fit and still recognize, damaged codes and bad fields
  refused, name clashes).
- Screenshots of the Share and Receive dialogs in both grimoires (found, not found,
  risky), and the book at 1000×680 with the new buttons.
- Simulated: receive a code → Browse to a local copy → add; receive a clashing file →
  Replace → editor opens; risky sigil needs *I trust*; damaged code shows an error; Share
  saves a file that loads back.
- Not yet: tried between two real Windows PCs.

---

## 2026-11-08 — Merged `tifanie-branch` into `jem-branch` (Jcelestra03, with Claude)

- Brought in Tifanie's even text layout and sigil sharing (Share / ✉ Receive, `.sigil`
  files and `SIGIL1-` codes) so `jem-branch` has everyone's work.
- Her branch already contained all of `jem-branch` (copied in, not branched from it), so
  the five files both sides touched (`manager.py`, `grimoire.py`, README, PLAN, LOG) were
  resolved with her versions; nothing from `jem-branch` was lost.
- Verified: all tests pass, and the Sigil Book opens with the grimoire, pens, Share and
  Receive.

---

## 2026-11-08 — Tutorial and "?" help (Jcelestra03, with Claude)

- **Guided tour** (`sigil/tutorial.py`): the first time the Sigil Book opens, a card asks
  "Want a quick tour?". *Show me around* walks through the grimoire switch, the Sigil
  Index, Inscribe, Cast, Test, Receive/Share and the hotkey/✦ button, outlining each part
  on the page with a card beside it (Back / Skip tour / Next). *Not now* closes it, and it
  doesn't come back on its own (`tutorial_seen` in settings.json). **✦ Tutorial** at the
  top of the window replays it.
- **Optional practice cast** at the end of the tour: draw a circle on the dimmed screen.
  It is checked against built-in practice shapes (circle, triangle, cross, lightning bolt,
  line), so nothing is saved or opened; the card says whether it read a circle and how
  closely. The last card offers *Inscribe my first sigil* when the book is empty.
- **"?" next to every button**: hover over it (or click it) for a one-or-two-sentence
  explanation. On the book: Grimoire, Sigil Index, the four actions, Edit / Test it /
  Share / Erase, Hotkey and Floating ✦ button. In the editor: Name, What it opens, the
  target, Your drawings, Pen, Size, Color, Clear, Undo, Add this drawing, Save sigil.
- `SigilApp.practice()` opens the overlay for a drawing that isn't cast (same "no overlay
  while a dialog holds a grab" rule as `summon`).

**Verified**
- `python -m unittest`: 47 tests pass (new `tests/test_tutorial.py`: every help key used
  exists, a hand-drawn circle is read as a circle and other shapes aren't, the tour starts
  once on first launch, every step outlines its part and has buttons, book buttons have
  help).
- Screenshots of every tour card in both grimoires, a tooltip, the practice result (a
  simulated circle, 72 % match), the editor's "?" marks, and a selected sigil's row.
- Not yet: someone new trying the tour for real.

---

## 2026-11-08 — Desktop Sigil.exe: install without Python (Jcelestra03, with Claude)

- Installing Python was the hardest step for people who don't use it, so
  `python build_exe.py` now builds **Desktop Sigil.exe** (PyInstaller, one folder) and
  zips it as `dist/Desktop-Sigil-Windows.zip` with a *How to open.txt*: unzip, double-click
  the .exe, and on the first run click *More info → Run anyway* past SmartScreen (the app
  isn't code-signed).
- The .exe keeps sigils and settings in `%APPDATA%\Desktop Sigil` (set by the launcher, so
  `store.py` is unchanged) so they survive replacing the folder with a newer build. Run
  from source, they stay next to the code as before.
- New app icon (a red seal with a ✦), drawn by `tools/make_icon.py` with the standard
  library; used for the .exe and every window.
- **PyInstaller is a build tool only**: the app still needs nothing outside the standard
  library. It still needs Tifanie's OK under our third-party rule (noted in PLAN).
- `build/` and `dist/` are gitignored.

**Verified**
- Built with Python 3.14.5 and PyInstaller 6.22.3 (zip: 12.9 MB). Unzipped into a clean
  folder and ran with an empty APPDATA: the Sigil Book opened with the seal icon and the
  first-launch tour, the hotkey registered, and settings.json was written to
  `%APPDATA%\Desktop Sigil`.
- `python -m unittest` passes.
- Not yet: tried on a PC that has never had Python installed.

---

## 2026-11-08 — Smoother window resizing (Jcelestra03, with Claude)

- Resizing the Sigil Book lagged: Tk repaints every canvas item for each step of a window
  drag, and the grimoire is ~1,600–2,600 items (rune writing, fur strands, beads), about
  180 ms per frame plus a full redraw whenever the mouse paused for 40 ms.
- While the size is changing, the small "detail" items (rune writing and fur/line strokes,
  tagged `detail`) are hidden, and the book is redrawn once, 150 ms after the size stops
  changing.
- The rune writing is now one text item per word instead of one per letter (1,368 → 393
  text items on Parchment). It draws the same random numbers, so nothing else moves.

**Verified**
- Simulated corner drag (40 steps): median **329 ms → 36 ms** per step on Parchment
  (289 → 35 ms on Obsidian); the full book is back ~0.35 s after letting go.
- Screenshot: the book looks the same as before. `python -m unittest` passes.

---

## 2026-11-08 — New grimoire: Candlelight and Midnight (Jcelestra03, with Claude)

- Jcelestra03 wanted a more realistic, anime-fantasy look. Four concepts were painted on a
  design canvas (Atelier sketchbook, Candlelit tome, Starlit grimoire, Living spell
  circle); the spell circle was picked, with the tome's candle lighting, in a light and a
  dark version.
- **Candlelight** (new default) and **Midnight** are painted pictures: a vellum (or black)
  grimoire on dark stone over a glowing emerald and gold rune circle, a candle's warm
  light falling off into shadow, gold corners, a red ribbon and a wax seal. tkinter can't
  paint soft light or grain, so `tools/render_art.py` draws the scene as SVG and has Edge
  (headless) save PNGs at 4 scales (`assets/grimoire/`, ~15 MB). `sigil/artbook.py`
  shows the scale that fits the window, centered; the picture fades to the canvas color at
  its edges, so big windows show no seam. Text, seals and buttons are drawn on top as before.
- Seals get a soft halo on the painted looks (`"glow"`), the selected index row uses
  faint rules instead of a solid band, and Erase has its own color (`"danger"`).
- **Parchment and Obsidian are kept** as the 3rd and 4th choices.
- New users start on Candlelight: `SETTINGS_DEFAULTS["theme"]` in `store.py` (Tifanie's
  file) changed from "parchment" to "candlelight". Existing settings keep their choice.

**Verified**
- `python -m unittest` passes (themes: all four share keys, every painted scale exists).
- Screenshots: both looks at 1160×760 with sigils, Candlelight at 1840×1000 (1.2 scale, no
  seams), the Midnight editor, the tour on Candlelight, and the rebuilt .exe (zip now
  28.6 MB) opening a fresh user into Candlelight.

---

## 2026-11-08 — Easier-to-read small text on Candlelight and Midnight (Jcelestra03, with Claude)

- Small text (sigil details, "Opens the program", hotkey and ✦ button lines, status) was
  hard to read on Candlelight: the candle's shadow darkened the lower right page, so the
  soft ink measured only 2.3:1 against it (4.5:1 is the usual minimum for small text).
- `tools/render_art.py`: the deep shadow now falls on the desk *around* the book; the
  pages get only a gentle candle warmth and a slight dimming far from it.
- Soft ink is a little stronger (Candlelight `#47331f`, Midnight `#bba06a`) and the
  painted looks use 11 pt instead of 10 pt for small and italic text.
- Result, measured on the art at each text spot: every one is 5.0:1 or better on both
  looks (was 2.3–6.0 on Candlelight, 2.7–5.0 on Midnight). Screenshots: same mood, the
  desk still falls into shadow. Tests pass; the .exe was rebuilt.

---

## 2026-11-08 — README rewritten as a user guide (Jcelestra03, with Claude)

- The GitHub home page now walks a new user through: install (download the zip from
  Releases → Extract All → Desktop Sigil.exe → past SmartScreen; or from source with
  Python), the first-launch tour and practice cast, picking a grimoire, making a first
  sigil, casting, every button, sharing, a troubleshooting table, and uninstalling.
  Developer notes moved to the end.
- Screenshots of Candlelight and Midnight added in `docs/`.
- Note: the install steps point to the Releases page; a release with
  `Desktop-Sigil-Windows.zip` attached still has to be published.
