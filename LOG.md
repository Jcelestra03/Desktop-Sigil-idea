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
