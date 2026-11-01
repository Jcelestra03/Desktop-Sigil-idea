"""Sigil Book: the main window. Add, edit, test and cast sigils without the terminal.

While this window is open (or minimized), the hotkey and the floating cast button work.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from . import actions, store
from .app import SigilApp
from .drawpad import DrawPad, draw_strokes
from .hotkey import parse as parse_hotkey, pretty
from .overlay import GLOW as GOLD_DARK, INK as GOLD, make_root
from .recognizer import DEFAULT_MIN_SCORE, Stroke, compare, recognize

BG = "#15132a"
PANEL = "#1f1c3a"
PANEL_HI = "#2c2852"
TEXT = "#e9e3ff"
MUTED = "#8c86a8"
DANGER = "#e58c8c"
INK_BG = "#0b0a1a"

FONT = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI Semibold", 12)
FONT_TITLE = ("Segoe UI Semibold", 22)

RECOMMENDED_SAMPLES = 3

TARGET_LABELS = {
    "app": "Program to open",
    "url": "Web address",
    "file": "File to open",
    "folder": "Folder to open",
}


def button(parent: tk.Misc, text: str, command, primary: bool = False,
           danger: bool = False, **kw) -> tk.Button:
    bg = GOLD if primary else PANEL_HI
    fg = INK_BG if primary else (DANGER if danger else TEXT)
    return tk.Button(parent, text=text, command=command, bg=bg, fg=fg, activebackground=fg,
                     activeforeground=bg, relief="flat", bd=0, padx=14, pady=6, font=FONT,
                     cursor="hand2", **kw)


def label(parent: tk.Misc, text: str = "", muted: bool = False, font=FONT,
          bg: str = BG, **kw) -> tk.Label:
    return tk.Label(parent, text=text, bg=bg, fg=MUTED if muted else TEXT, font=font,
                    anchor="w", justify="left", **kw)


class SigilBook:
    def __init__(self) -> None:
        root = self.root = make_root()
        root.title("Desktop Sigil — Sigil Book")
        root.configure(bg=BG)
        root.geometry("760x600")
        root.minsize(600, 440)
        root.protocol("WM_DELETE_WINDOW", self.quit)

        self.settings = store.load_settings()
        self.app = SigilApp(root, on_status=self.set_status)
        self.orb: CastOrb | None = None

        self._build()
        self.refresh()
        self.apply_hotkey(self.settings["hotkey"], initial=True)
        if self.settings["orb"]:
            self.show_orb()
        root.deiconify()

    # ---- layout -------------------------------------------------------------

    def _build(self) -> None:
        root = self.root
        header = tk.Frame(root, bg=BG, padx=24, pady=18)
        header.pack(fill="x")
        tk.Label(header, text="✦ Sigil Book", bg=BG, fg=GOLD, font=FONT_TITLE).pack(anchor="w")
        label(header, "Draw a sigil to open a program, website, file or folder.",
              muted=True).pack(anchor="w")

        toolbar = tk.Frame(root, bg=BG, padx=24)
        toolbar.pack(fill="x")
        button(toolbar, "+  New sigil", self.new_sigil, primary=True).pack(side="left")
        button(toolbar, "✦  Cast a sigil", lambda: self.app.summon()).pack(side="left", padx=8)
        button(toolbar, "Test a drawing", lambda: self.app.summon(dry_run=True)).pack(side="left")

        # Scrollable list of sigils
        holder = tk.Frame(root, bg=BG, padx=24, pady=14)
        holder.pack(fill="both", expand=True)
        self.list_canvas = tk.Canvas(holder, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(holder, orient="vertical", command=self.list_canvas.yview)
        self.list_canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.list_canvas.pack(side="left", fill="both", expand=True)
        self.list_frame = tk.Frame(self.list_canvas, bg=BG)
        window = self.list_canvas.create_window(0, 0, window=self.list_frame, anchor="nw")
        self.list_frame.bind("<Configure>", lambda e: self.list_canvas.configure(
            scrollregion=self.list_canvas.bbox("all")))
        self.list_canvas.bind("<Configure>", lambda e: self.list_canvas.itemconfigure(
            window, width=e.width))
        self.list_canvas.bind("<Enter>", lambda e: root.bind_all("<MouseWheel>", self._wheel))
        self.list_canvas.bind("<Leave>", lambda e: root.unbind_all("<MouseWheel>"))

        footer = tk.Frame(root, bg=PANEL, padx=24, pady=10)
        footer.pack(fill="x", side="bottom")
        self.status = label(footer, "Ready.", muted=True, bg=PANEL)
        self.status.pack(side="left", fill="x", expand=True)
        self.orb_var = tk.BooleanVar(value=self.settings["orb"])
        tk.Checkbutton(footer, text="Floating cast button", variable=self.orb_var,
                       command=self.toggle_orb, bg=PANEL, fg=TEXT, selectcolor=PANEL_HI,
                       activebackground=PANEL, activeforeground=TEXT, font=FONT_SMALL,
                       cursor="hand2").pack(side="right")
        tk.Button(footer, text="Change", command=self.change_hotkey, bg=PANEL, fg=GOLD,
                  activebackground=PANEL, activeforeground=TEXT, relief="flat", bd=0,
                  font=FONT_SMALL, cursor="hand2").pack(side="right", padx=(4, 16))
        self.hotkey_label = label(footer, "", muted=True, bg=PANEL, font=FONT_SMALL)
        self.hotkey_label.pack(side="right")

    def _wheel(self, event: tk.Event) -> None:
        self.list_canvas.yview_scroll(int(-event.delta / 120), "units")

    def refresh(self) -> None:
        self.sigils = store.load()
        for child in self.list_frame.winfo_children():
            child.destroy()
        if not self.sigils:
            label(self.list_frame, "No sigils yet.\n\nClick “New sigil”, choose what it opens, "
                  "and draw a shape for it.", muted=True, pady=40).pack(fill="x")
            return
        for sigil in self.sigils:
            self._row(sigil)

    def _row(self, sigil: store.Sigil) -> None:
        row = tk.Frame(self.list_frame, bg=PANEL, padx=12, pady=10)
        row.pack(fill="x", pady=4)
        thumb = tk.Canvas(row, width=64, height=64, bg=INK_BG, highlightthickness=0)
        thumb.pack(side="left")
        if sigil.templates:
            draw_strokes(thumb, sigil.templates[0], 8, 8, 48, 48, GOLD, 2)

        text = tk.Frame(row, bg=PANEL, padx=14)
        text.pack(side="left", fill="x", expand=True)
        label(text, sigil.name, font=FONT_BOLD, bg=PANEL).pack(anchor="w")
        kind = actions.KINDS.get(sigil.action["type"], sigil.action["type"])
        label(text, f"{kind}  ·  {sigil.action['target']}", muted=True, bg=PANEL,
              font=FONT_SMALL).pack(anchor="w", fill="x")
        samples = len(sigil.templates)
        label(text, f"{samples} drawing{'s' if samples != 1 else ''}", muted=True, bg=PANEL,
              font=FONT_SMALL).pack(anchor="w")

        button(row, "Delete", lambda: self.delete(sigil), danger=True).pack(side="right")
        button(row, "Edit", lambda: self.edit(sigil)).pack(side="right", padx=8)
        for widget in (row, thumb, text, *text.winfo_children()):
            widget.bind("<Double-Button-1>", lambda e: self.edit(sigil))

    # ---- actions ------------------------------------------------------------

    def set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def new_sigil(self) -> None:
        SigilEditor(self, None)

    def edit(self, sigil: store.Sigil) -> None:
        SigilEditor(self, sigil)

    def delete(self, sigil: store.Sigil) -> None:
        if not messagebox.askyesno("Delete sigil", f"Delete “{sigil.name}”?", parent=self.root):
            return
        sigils = [s for s in store.load() if s.name != sigil.name]
        store.save(sigils)
        self.refresh()
        self.set_status(f"Deleted {sigil.name}.")

    def apply_hotkey(self, hotkey: str, initial: bool = False) -> bool:
        try:
            self.app.set_hotkey(hotkey)
        except (ValueError, OSError) as e:
            reason = str(e) if isinstance(e, ValueError) else \
                f"{pretty(hotkey)} is already used by another program."
            if initial:
                self.hotkey_label.configure(text=f"Hotkey off ({pretty(hotkey)} is taken)")
                self.set_status("Click “Change” to pick a different hotkey.")
            else:
                messagebox.showerror("Hotkey", reason, parent=self.root)
            return False
        self.hotkey_label.configure(text=f"Hotkey: {pretty(hotkey)}")
        self.settings["hotkey"] = hotkey
        store.save_settings(self.settings)
        return True

    def change_hotkey(self) -> None:
        current = self.app.hotkey.hotkey if self.app.hotkey else self.settings["hotkey"]
        answer = simpledialog.askstring(
            "Change hotkey",
            "Type a shortcut, for example  ctrl+alt+s  or  win+alt+q\n"
            "Modifiers: ctrl, alt, shift, win.  Keys: a–z, 0–9, space, f1–f12.",
            initialvalue=current, parent=self.root)
        if answer:
            answer = answer.strip().lower()
            try:
                parse_hotkey(answer)
            except ValueError as e:
                messagebox.showerror("Hotkey", str(e), parent=self.root)
                return
            if self.apply_hotkey(answer):
                self.set_status(f"Hotkey is now {pretty(answer)}.")

    def show_orb(self) -> None:
        if self.orb is None:
            self.orb = CastOrb(self)

    def toggle_orb(self) -> None:
        on = self.orb_var.get()
        if on:
            self.show_orb()
        elif self.orb:
            self.orb.win.destroy()
            self.orb = None
        self.settings["orb"] = on
        store.save_settings(self.settings)

    def save_orb_position(self, x: int, y: int) -> None:
        self.settings["orb_pos"] = [x, y]
        store.save_settings(self.settings)

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit(self) -> None:
        self.app.stop()
        self.root.destroy()

    def mainloop(self) -> None:
        self.root.mainloop()


class SigilEditor:
    """Dialog to create or edit one sigil: name, what it opens, and its drawings."""

    def __init__(self, book: SigilBook, sigil: store.Sigil | None):
        self.book = book
        self.original = sigil
        self.samples: list[list[Stroke]] = [list(t) for t in sigil.templates] if sigil else []

        win = self.win = tk.Toplevel(book.root, bg=BG, padx=24, pady=20)
        win.title("Edit sigil" if sigil else "New sigil")
        win.transient(book.root)
        win.resizable(False, False)

        form = tk.Frame(win, bg=BG)
        form.grid(row=0, column=0, sticky="nw", padx=(0, 28))
        label(form, "Name").pack(anchor="w")
        self.name_var = tk.StringVar(value=sigil.name if sigil else "")
        self._entry(form, self.name_var).pack(anchor="w", fill="x", pady=(2, 14))

        label(form, "When I draw it, open a…").pack(anchor="w")
        self.kind_var = tk.StringVar(value=sigil.action["type"] if sigil else "app")
        for kind, text in actions.KINDS.items():
            tk.Radiobutton(form, text=text, value=kind, variable=self.kind_var,
                           command=self._kind_changed, bg=BG, fg=TEXT, selectcolor=PANEL_HI,
                           activebackground=BG, activeforeground=GOLD, font=FONT,
                           cursor="hand2").pack(anchor="w")

        self.target_label = label(form)
        self.target_label.pack(anchor="w", pady=(14, 0))
        target_row = tk.Frame(form, bg=BG)
        target_row.pack(anchor="w", fill="x", pady=2)
        self.target_var = tk.StringVar(value=sigil.action["target"] if sigil else "")
        self._entry(target_row, self.target_var, width=30).pack(side="left")
        self.browse_btn = button(target_row, "Browse…", self.browse)
        self.browse_btn.pack(side="left", padx=(6, 0))
        self.target_hint = label(form, muted=True, font=FONT_SMALL, wraplength=300)
        self.target_hint.pack(anchor="w")

        pad_col = tk.Frame(win, bg=BG)
        pad_col.grid(row=0, column=1, sticky="n")
        label(pad_col, "Draw the sigil").pack(anchor="w")
        label(pad_col, f"Draw it {RECOMMENDED_SAMPLES} times the same way so it's easy to "
              "recognize.", muted=True, font=FONT_SMALL).pack(anchor="w", pady=(0, 6))
        self.pad = DrawPad(pad_col, size=300, bg=INK_BG, guide=PANEL_HI,
                           on_change=self._update_buttons)
        self.pad.pack()
        pad_buttons = tk.Frame(pad_col, bg=BG)
        pad_buttons.pack(fill="x", pady=8)
        button(pad_buttons, "Clear", self.pad.clear).pack(side="left")
        self.add_btn = button(pad_buttons, "Add this drawing", self.add_sample, primary=True)
        self.add_btn.pack(side="right")
        self.samples_frame = tk.Frame(pad_col, bg=BG)
        self.samples_frame.pack(fill="x")

        bottom = tk.Frame(win, bg=BG)
        bottom.grid(row=1, column=0, columnspan=2, sticky="e", pady=(18, 0))
        button(bottom, "Cancel", win.destroy).pack(side="left", padx=8)
        button(bottom, "Save sigil", self.save, primary=True).pack(side="left")

        win.bind("<Escape>", lambda e: win.destroy())
        self._kind_changed()
        self._render_samples()
        win.grab_set()
        win.focus_force()

    def _entry(self, parent: tk.Misc, var: tk.StringVar, width: int = 38) -> tk.Entry:
        return tk.Entry(parent, textvariable=var, width=width, bg=PANEL, fg=TEXT,
                        insertbackground=GOLD, relief="flat", font=FONT,
                        highlightthickness=1, highlightbackground=PANEL_HI,
                        highlightcolor=GOLD)

    def _kind_changed(self) -> None:
        kind = self.kind_var.get()
        self.target_label.configure(text=TARGET_LABELS[kind])
        hints = {
            "app": "Pick an .exe, or a shortcut (.lnk) from your desktop or Start menu.",
            "url": "For example  canvas.uw.edu  or  https://www.youtube.com",
            "file": "Any document, picture, etc. Opens in its usual program.",
            "folder": "Opens in File Explorer.",
        }
        self.target_hint.configure(text=hints[kind])
        if kind == "url":
            self.browse_btn.pack_forget()
        else:
            self.browse_btn.pack(side="left", padx=(6, 0))

    def browse(self) -> None:
        kind = self.kind_var.get()
        if kind == "folder":
            path = filedialog.askdirectory(parent=self.win, title="Choose a folder")
        elif kind == "app":
            path = filedialog.askopenfilename(
                parent=self.win, title="Choose a program",
                filetypes=[("Programs and shortcuts", "*.exe *.lnk *.bat *.cmd *.url"),
                           ("All files", "*.*")])
        else:
            path = filedialog.askopenfilename(parent=self.win, title="Choose a file")
        if path:
            self.target_var.set(os.path.normpath(path))
            if not self.name_var.get().strip():
                self.name_var.set(os.path.splitext(os.path.basename(path))[0])

    def add_sample(self) -> None:
        drawing = self.pad.drawing
        if not drawing:
            return
        self.samples.append(drawing)
        self.pad.clear()
        self._render_samples()

    def remove_sample(self, index: int) -> None:
        del self.samples[index]
        self._render_samples()

    def _render_samples(self) -> None:
        for child in self.samples_frame.winfo_children():
            child.destroy()
        n = len(self.samples)
        text = (f"{n} of {RECOMMENDED_SAMPLES} drawings" if n < RECOMMENDED_SAMPLES
                else f"{n} drawings ✓") + ("  ·  click one to remove it" if n else "")
        label(self.samples_frame, text, muted=True, font=FONT_SMALL).pack(anchor="w")
        strip = tk.Frame(self.samples_frame, bg=BG)
        strip.pack(anchor="w", pady=4)
        for i, sample in enumerate(self.samples):
            thumb = tk.Canvas(strip, width=52, height=52, bg=INK_BG, highlightthickness=1,
                              highlightbackground=PANEL_HI, cursor="hand2")
            thumb.pack(side="left", padx=(0, 6))
            draw_strokes(thumb, sample, 6, 6, 40, 40, GOLD, 2)
            thumb.bind("<Button-1>", lambda e, i=i: self.remove_sample(i))
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.add_btn.configure(state="normal" if self.pad.drawing else "disabled")

    def save(self) -> None:
        win = self.win
        name = self.name_var.get().strip()
        kind = self.kind_var.get()
        target = actions.normalize_target(kind, self.target_var.get())
        if self.pad.drawing:  # a drawing on the pad that wasn't added yet still counts
            self.add_sample()

        sigils = store.load()
        clash = store.find(sigils, name)
        problem = None
        if not name:
            problem = "Give the sigil a name."
        elif clash and (self.original is None or clash.name != self.original.name):
            problem = f"There's already a sigil called “{clash.name}”."
        elif not target:
            problem = f"Fill in “{TARGET_LABELS[kind]}”."
        elif kind in ("file", "folder") and not os.path.exists(target):
            problem = f"Can't find {target}."
        elif kind == "app" and os.path.isabs(target) and not os.path.exists(target):
            problem = f"Can't find {target}."
        elif not self.samples:
            problem = "Draw the sigil, then click “Add this drawing”."
        if problem:
            messagebox.showwarning("Almost there", problem, parent=win)
            return

        if len(self.samples) < RECOMMENDED_SAMPLES and not messagebox.askyesno(
                "Save sigil",
                f"You've drawn it {len(self.samples)} time{'s' if len(self.samples) != 1 else ''}. "
                f"Drawing it {RECOMMENDED_SAMPLES} times helps it get recognized.\n\n"
                "Save anyway?", parent=win):
            return

        others = [s for s in sigils if self.original is None or s.name != self.original.name]
        lookalike = recognize(self.samples[-1], others, min_score=DEFAULT_MIN_SCORE + 0.1)
        if lookalike and not messagebox.askyesno(
                "Save sigil",
                f"This looks a lot like “{lookalike.sigil.name}”, so they may get mixed up.\n\n"
                "Save anyway?", parent=win):
            return
        if len(self.samples) > 1 and min(compare(self.samples[0], s)
                                         for s in self.samples[1:]) < DEFAULT_MIN_SCORE:
            if not messagebox.askyesno(
                    "Save sigil",
                    "Your drawings look quite different from each other. Remove the odd one "
                    "out (click it) for better recognition.\n\nSave anyway?", parent=win):
                return

        sigil = store.Sigil(name, {"type": kind, "target": target}, self.samples)
        if self.original is None:
            others.append(sigil)
        else:
            i = next(i for i, s in enumerate(sigils) if s.name == self.original.name)
            others.insert(i, sigil)
        store.save(others)
        self.book.refresh()
        self.book.set_status(f"Saved {name}.")
        win.destroy()


class CastOrb:
    """Small always-on-top button. Click to cast, drag to move, right-click for a menu."""

    SIZE = 60
    KEY = "#ff00fe"  # transparent color, gives the window a round shape

    def __init__(self, book: SigilBook):
        self.book = book
        win = self.win = tk.Toplevel(book.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-transparentcolor", self.KEY)
        size = self.SIZE
        pos = book.settings.get("orb_pos")
        x, y = pos if pos else (win.winfo_screenwidth() - size - 40,
                                win.winfo_screenheight() - size - 120)
        win.geometry(f"{size}x{size}+{x}+{y}")

        canvas = tk.Canvas(win, width=size, height=size, bg=self.KEY, highlightthickness=0,
                           cursor="hand2")
        canvas.pack()
        canvas.create_oval(3, 3, size - 3, size - 3, fill=PANEL, outline=GOLD, width=3)
        canvas.create_text(size / 2, size / 2, text="✦", fill=GOLD, font=("Segoe UI", 20))

        self.menu = tk.Menu(win, tearoff=False)
        self.menu.add_command(label="Cast a sigil", command=lambda: book.app.summon())
        self.menu.add_command(label="Open Sigil Book", command=book.show)
        self.menu.add_separator()
        self.menu.add_command(label="Hide this button", command=self._hide)

        canvas.bind("<ButtonPress-1>", self._press)
        canvas.bind("<B1-Motion>", self._drag)
        canvas.bind("<ButtonRelease-1>", self._release)
        canvas.bind("<Button-3>", lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self._start = (0, 0, 0, 0)
        self._dragging = False

    def _press(self, event: tk.Event) -> None:
        self._start = (event.x_root, event.y_root, self.win.winfo_x(), self.win.winfo_y())
        self._dragging = False

    def _drag(self, event: tk.Event) -> None:
        sx, sy, wx, wy = self._start
        dx, dy = event.x_root - sx, event.y_root - sy
        if self._dragging or abs(dx) + abs(dy) > 5:
            self._dragging = True
            self.win.geometry(f"+{wx + dx}+{wy + dy}")

    def _release(self, event: tk.Event) -> None:
        if self._dragging:
            self.book.save_orb_position(self.win.winfo_x(), self.win.winfo_y())
        else:
            self.book.app.summon()

    def _hide(self) -> None:
        self.book.orb_var.set(False)
        self.book.toggle_orb()


def main() -> None:
    SigilBook().mainloop()
