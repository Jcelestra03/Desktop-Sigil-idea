"""Double-click this file to open Desktop Sigil (no terminal window)."""

import traceback
from pathlib import Path

try:
    from sigil.manager import main

    main()
except Exception:
    # pythonw has no console, so show crashes instead of failing silently
    log = Path(__file__).with_name("sigil-error.log")
    log.write_text(traceback.format_exc(), encoding="utf-8")
    import tkinter.messagebox

    tkinter.messagebox.showerror(
        "Desktop Sigil", f"Something went wrong. Details were saved to:\n{log}")
