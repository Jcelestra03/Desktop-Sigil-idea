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
