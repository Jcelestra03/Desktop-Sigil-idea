"""Build Desktop Sigil.exe, so people can use the app without installing Python.

For developers only (the app itself stays standard library only). Needs PyInstaller:

    python -m pip install pyinstaller
    python build_exe.py

Output:
    dist/Desktop Sigil/                the app: Desktop Sigil.exe + an _internal folder
    dist/Desktop-Sigil-Windows.zip     that folder zipped, to send to someone

The person who gets the zip: unzip it, open the folder, double-click Desktop Sigil.exe.
Their sigils and settings are kept in %APPDATA%\\Desktop Sigil.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
APP = DIST / "Desktop Sigil"
ZIP = DIST / "Desktop-Sigil-Windows.zip"

HOW_TO = """Desktop Sigil
=============

1. Double-click "Desktop Sigil.exe" (in this folder).

   The first time, Windows may say "Windows protected your PC". That's because the app
   isn't signed by a big company. Click "More info", then "Run anyway".

2. The Sigil Book opens and offers a quick tour. Every button has a small ? next to it:
   hover over it for a short explanation.

Tip: right-click "Desktop Sigil.exe" > "Show more options" > "Send to" > "Desktop
(create shortcut)" to put it on your desktop. Keep the _internal folder next to the .exe.

Your sigils and settings are saved in %APPDATA%\\Desktop Sigil, so they stay when you
replace this folder with a newer version.
"""


def main() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        sys.exit("PyInstaller isn't installed. Run:  python -m pip install pyinstaller")

    subprocess.run([sys.executable, str(ROOT / "tools" / "make_icon.py")], check=True)
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
        "--name", "Desktop Sigil",
        "--icon", str(ROOT / "assets" / "sigil.ico"),
        "--add-data", f"{ROOT / 'assets'};assets",
        "--distpath", str(DIST), "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        str(ROOT / "Desktop Sigil.pyw"),
    ], check=True, cwd=ROOT)

    (APP / "How to open.txt").write_text(HOW_TO, encoding="utf-8")
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(APP.rglob("*")):
            z.write(path, Path("Desktop Sigil") / path.relative_to(APP))
    size = ZIP.stat().st_size / 1e6
    print(f"\nBuilt {APP / 'Desktop Sigil.exe'}\nZipped {ZIP} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
