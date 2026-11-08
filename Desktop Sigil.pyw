"""Double-click this file to open Desktop Sigil (no terminal window).

It is also the entry point of the built Desktop Sigil.exe (see build_exe.py). The .exe
keeps sigils and settings in %APPDATA%\\Desktop Sigil, so they survive replacing the
app folder with a newer build; run from source, they stay next to the code as before.
"""

import os
import sys
import traceback
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)  # running as Desktop Sigil.exe
if FROZEN:
    DATA = Path(os.environ.get("APPDATA") or Path.home()) / "Desktop Sigil"
    DATA.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("SIGIL_FILE", str(DATA / "sigils.json"))
    LOG = DATA / "sigil-error.log"
else:
    LOG = Path(__file__).with_name("sigil-error.log")

try:
    from sigil.manager import main

    main()
except Exception:
    # pythonw has no console, so show crashes instead of failing silently
    LOG.write_text(traceback.format_exc(), encoding="utf-8")
    import tkinter.messagebox

    tkinter.messagebox.showerror(
        "Desktop Sigil", f"Something went wrong. Details were saved to:\n{LOG}")
