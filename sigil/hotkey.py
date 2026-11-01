"""Windows global hotkey via Win32 RegisterHotKey, on a background thread.

The callback runs on that background thread, so it must not touch tkinter directly;
app.py hands work to the main thread through a queue.
"""

from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from typing import Callable

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
VK_SPACE = 0x20
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

DEFAULT_HOTKEY = "ctrl+alt+s"  # "S for sigil"; ctrl+alt+space was already taken on a dev machine

_MODIFIERS = {"ctrl": MOD_CONTROL, "alt": MOD_ALT, "shift": MOD_SHIFT, "win": MOD_WIN}
_KEYS = {"space": VK_SPACE, **{f"f{i}": 0x6F + i for i in range(1, 13)}}

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


def parse(hotkey: str) -> tuple[int, int]:
    """'ctrl+alt+space' -> (modifiers, virtual key). Keys: a-z, 0-9, space, f1-f12."""
    *mods, key = hotkey.lower().replace(" ", "").split("+")
    try:
        modifiers = 0
        for m in mods:
            modifiers |= _MODIFIERS[m]
    except KeyError as e:
        raise ValueError(f"Unknown modifier {e} in {hotkey!r} (use ctrl, alt, shift, win)") from None
    if key in _KEYS:
        vk = _KEYS[key]
    elif len(key) == 1 and key.isalnum():
        vk = ord(key.upper())
    else:
        raise ValueError(f"Unknown key {key!r} in {hotkey!r}")
    if not modifiers:
        raise ValueError("A hotkey needs at least one modifier (ctrl, alt, shift, win)")
    return modifiers, vk


class HotkeyListener:
    def __init__(self, callback: Callable[[], None], hotkey: str = DEFAULT_HOTKEY):
        self.callback = callback
        self.hotkey = hotkey
        modifiers, self.vk = parse(hotkey)
        self.modifiers = modifiers | MOD_NOREPEAT
        self._thread_id: int | None = None
        self._registered = threading.Event()
        self._error: int | None = None

    def start(self) -> None:
        """Start listening. Raises OSError if the hotkey is taken by another program."""
        threading.Thread(target=self._loop, daemon=True).start()
        self._registered.wait()
        if self._error is not None:
            raise ctypes.WinError(self._error)

    def stop(self) -> None:
        if self._thread_id is not None:
            _user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)

    def _loop(self) -> None:
        # The hotkey belongs to the thread that registers it, so register here.
        self._thread_id = _kernel32.GetCurrentThreadId()
        if not _user32.RegisterHotKey(None, 1, self.modifiers, self.vk):
            self._error = ctypes.get_last_error()
            self._registered.set()
            return
        self._registered.set()
        try:
            msg = wintypes.MSG()
            while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY:
                    self.callback()
        finally:
            _user32.UnregisterHotKey(None, 1)
