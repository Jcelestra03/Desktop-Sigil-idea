"""The Share and Receive dialogs of the Sigil Book (the logic lives in share.py).

Share: save the selected sigil as a .sigil file, or copy it as a text code.
Receive: open a .sigil file or paste a code, check what it opens on this computer,
show anything worth a second look, then add it to the book. Nothing runs on import.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

from . import actions, share, store
from .drawpad import draw_strokes
from .manager import OPENS, SigilEditor, TARGET_LABELS, button, label

if TYPE_CHECKING:
    from .manager import SigilBook

FILE_TYPES = [("Sigils", "*" + share.FILE_EXT), ("All files", "*.*")]


def _dialog(book: SigilBook, title: str) -> tk.Toplevel:
    t = book.theme
    win = tk.Toplevel(book.root, bg=t["page"], padx=28, pady=18, highlightthickness=3,
                      highlightbackground=t["gilt"], highlightcolor=t["gilt"])
    win.title(title)
    win.transient(book.root)
    win.resizable(False, False)
    win.bind("<Escape>", lambda e: win.destroy())
    return win


def _center(win: tk.Toplevel, root: tk.Misc) -> None:
    win.update_idletasks()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    x = root.winfo_rootx() + (root.winfo_width() - w) // 2
    y = root.winfo_rooty() + (root.winfo_height() - h) // 2
    x = max(0, min(x, win.winfo_screenwidth() - w))
    y = max(0, min(y, win.winfo_screenheight() - h - 48))
    win.geometry(f"+{x}+{y}")


def _entry(parent: tk.Misc, var: tk.StringVar, t: dict, width: int = 40) -> tk.Entry:
    return tk.Entry(parent, textvariable=var, width=width, bg=t["field"], fg=t["ink"],
                    insertbackground=t["accent"], relief="flat", font=t["font_body"],
                    highlightthickness=1, highlightbackground=t["field_line"],
                    highlightcolor=t["accent"], disabledbackground=t["page"],
                    disabledforeground=t["ink_soft"])


def _text_box(parent: tk.Misc, t: dict, height: int) -> tk.Text:
    return tk.Text(parent, width=56, height=height, wrap="char", bg=t["field"], fg=t["ink"],
                   insertbackground=t["accent"], relief="flat", font=("Consolas", 9),
                   highlightthickness=1, highlightbackground=t["field_line"],
                   highlightcolor=t["accent"], padx=6, pady=4)


def _check(parent: tk.Misc, text: str, var: tk.BooleanVar, t: dict, command=None,
           **kw) -> tk.Checkbutton:
    return tk.Checkbutton(parent, text=text, variable=var, command=command, bg=t["page"],
                          fg=t["ink"], selectcolor=t["field"], activebackground=t["page"],
                          activeforeground=t["accent"], font=t["font_body"], anchor="w",
                          justify="left", cursor="hand2", highlightthickness=0, **kw)


def _preview(parent: tk.Misc, t: dict, templates, style: dict, size: int = 150) -> tk.Canvas:
    c = tk.Canvas(parent, width=size, height=size, bg=t["page"], highlightthickness=0)
    r = size / 2 - 3
    c.create_oval(3, 3, size - 3, size - 3, outline=t["accent"], width=3)
    c.create_oval(10, 10, size - 10, size - 10, outline=t["accent"])
    box = (r - 7) * 0.68
    if templates:
        draw_strokes(c, templates[0], size / 2 - box, size / 2 - box, box * 2, box * 2,
                     t["accent"], 3, style=style or None, bg=t["page"])
    return c


# ---- Share -----------------------------------------------------------------------

class ShareDialog:
    def __init__(self, book: SigilBook, sigil: store.Sigil):
        self.book, self.sigil = book, sigil
        self.t = t = book.theme
        win = self.win = _dialog(book, f"Share {sigil.name}")

        top = tk.Frame(win, bg=t["page"])
        top.pack(fill="x")
        _preview(top, t, sigil.templates, sigil.style, 110).pack(side="left", padx=(0, 18))
        info = tk.Frame(top, bg=t["page"])
        info.pack(side="left", fill="x", expand=True)
        label(info, f"Share “{sigil.name}”", t, font="head").pack(anchor="w")
        label(info, "Send it to a friend. When they add it to their Desktop Sigil, it opens\n"
                    "the same thing on their computer.", t, muted=True,
              font="small").pack(anchor="w")
        shared = share.portable_target(sigil.action["type"], sigil.action["target"])
        label(info, f"{OPENS.get(sigil.action['type'], 'Opens')}:  {shared}", t, font="small",
              wraplength=420).pack(anchor="w", pady=(6, 0))
        for note in share.sender_notes(sigil):
            label(info, note, t, muted=True, font="italic", wraplength=420).pack(anchor="w",
                                                                                pady=(4, 0))

        label(win, "As a file", t).pack(anchor="w", pady=(18, 0))
        label(win, "Save it, then send the .sigil file by email, Discord or a USB stick.", t,
              muted=True, font="small").pack(anchor="w")
        row = tk.Frame(win, bg=t["page"])
        row.pack(fill="x", pady=(6, 0))
        button(row, "Save .sigil file…", self.save_file, t).pack(side="left")
        self.file_status = label(row, "", t, muted=True, font="small")
        self.file_status.pack(side="left", padx=10)

        self.code = share.to_code(sigil)
        label(win, "As a text code", t).pack(anchor="w", pady=(18, 0))
        label(win, f"Copy it and paste it into a message ({len(self.code)} characters, fits in "
                   "one Discord message).", t, muted=True, font="small").pack(anchor="w")
        box = _text_box(win, t, height=min(8, len(self.code) // 56 + 1))
        box.insert("1.0", self.code)
        box.configure(state="disabled")
        box.pack(anchor="w", fill="x", pady=(6, 0))
        row = tk.Frame(win, bg=t["page"])
        row.pack(fill="x", pady=(6, 0))
        button(row, "Copy code", self.copy_code, t, primary=True).pack(side="left")
        self.code_status = label(row, "", t, muted=True, font="small")
        self.code_status.pack(side="left", padx=10)

        bottom = tk.Frame(win, bg=t["page"])
        bottom.pack(fill="x", pady=(18, 0))
        button(bottom, "Done", win.destroy, t).pack(side="right")

        _center(win, book.root)
        win.grab_set()
        win.focus_force()

    def save_file(self) -> None:
        safe = "".join(ch for ch in self.sigil.name if ch not in '<>:"/\\|?*').strip() or "sigil"
        path = filedialog.asksaveasfilename(parent=self.win, title="Save sigil",
                                            defaultextension=share.FILE_EXT,
                                            initialfile=safe + share.FILE_EXT,
                                            filetypes=FILE_TYPES)
        if not path:
            return
        try:
            share.save_file(self.sigil, path)
        except OSError as e:
            messagebox.showerror("Share", f"Couldn't save the file: {e.strerror or e}",
                                 parent=self.win)
            return
        self.file_status.configure(text=f"Saved {os.path.basename(path)}")
        self.book.set_status(f"Saved {self.sigil.name} as {os.path.basename(path)}.")

    def copy_code(self) -> None:
        self.win.clipboard_clear()
        self.win.clipboard_append(self.code)
        self.code_status.configure(text="Copied! Paste it into a message.")
        self.book.set_status(f"Copied the code for {self.sigil.name}.")


# ---- Receive -----------------------------------------------------------------------

class ReceiveDialog:
    def __init__(self, book: SigilBook):
        self.book = book
        self.t = book.theme
        self.win = _dialog(book, "Receive a sigil")
        self.body: tk.Frame | None = None
        self._ask()
        _center(self.win, book.root)
        self.win.grab_set()
        self.win.focus_force()

    def _fresh(self) -> tk.Frame:
        if self.body:
            self.body.destroy()
        self.body = tk.Frame(self.win, bg=self.t["page"])
        self.body.pack(fill="both", expand=True)
        return self.body

    # step 1: where does it come from?

    def _ask(self) -> None:
        t, body = self.t, self._fresh()
        label(body, "Receive a sigil", t, font="head").pack(anchor="w")
        label(body, "Open a .sigil file someone sent you, or paste their sigil code.", t,
              muted=True, font="small").pack(anchor="w")

        button(body, "Open a .sigil file…", self.open_file, t).pack(anchor="w", pady=(14, 0))

        label(body, "Or paste a sigil code", t).pack(anchor="w", pady=(18, 0))
        self.code_box = _text_box(body, t, height=6)
        self.code_box.pack(anchor="w", fill="x", pady=(4, 0))
        try:  # a copied code is probably what they want
            clip = self.win.clipboard_get()
            if share.find_code(clip):
                self.code_box.insert("1.0", clip.strip())
        except tk.TclError:
            pass
        self.error = label(body, "", t, font="small", wraplength=460)
        self.error.configure(fg=t["accent"])
        self.error.pack(anchor="w", pady=(4, 0))

        row = tk.Frame(body, bg=t["page"])
        row.pack(fill="x", pady=(10, 0))
        button(row, "Read code", self.read_code, t, primary=True).pack(side="right")
        button(row, "Cancel", self.win.destroy, t).pack(side="right", padx=8)
        self.code_box.focus_set()
        self.win.bind("<Return>", lambda e: self.read_code() if self.body and
                      self.code_box.winfo_exists() else None)

    def open_file(self) -> None:
        path = filedialog.askopenfilename(parent=self.win, title="Open a sigil",
                                          filetypes=FILE_TYPES)
        if path:
            self._load(lambda: share.load_file(path))

    def read_code(self) -> str:
        self._load(lambda: share.from_code(self.code_box.get("1.0", "end")))
        return "break"

    def _load(self, read) -> None:
        try:
            received = read()
        except share.ShareError as e:
            self.error.configure(text=str(e))
            return
        self.win.unbind("<Return>")
        self._review(received)

    # step 2: check it, then add it

    def _review(self, got: share.Received) -> None:
        t, body = self.t, self._fresh()
        self.got = got
        existing = [s.name for s in store.load()]
        self.clash = store.find(store.load(), got.name)

        top = tk.Frame(body, bg=t["page"])
        top.pack(fill="x")
        _preview(top, t, got.templates, got.style).pack(side="left", padx=(0, 20))
        info = tk.Frame(top, bg=t["page"])
        info.pack(side="left", fill="both", expand=True)
        label(info, f"“{got.name}”", t, font="head").pack(anchor="w")
        n = len(got.templates)
        label(info, f"{actions.KINDS[got.kind]} · {n} drawing{'s' if n != 1 else ''}", t,
              muted=True, font="small").pack(anchor="w")

        label(info, "Name in your book", t).pack(anchor="w", pady=(10, 0))
        self.name_var = tk.StringVar(value=share.free_name(got.name, existing))
        self.name_entry = _entry(info, self.name_var, t, width=34)
        self.name_entry.pack(anchor="w", pady=(2, 0))
        self.replace_var = tk.BooleanVar(value=False)
        if self.clash:
            label(info, f"You already have a sigil called “{self.clash.name}”.", t, muted=True,
                  font="small").pack(anchor="w", pady=(4, 0))
            _check(info, f"Replace my “{self.clash.name}” instead", self.replace_var, t,
                   command=self._replace_changed).pack(anchor="w")

        # where it points on this computer
        label(body, TARGET_LABELS[got.kind], t).pack(anchor="w", pady=(16, 0))
        target, found = share.find_target(got.kind, got.shared_target)
        self.target_var = tk.StringVar(value=target)
        row = tk.Frame(body, bg=t["page"])
        row.pack(fill="x", pady=(2, 0))
        _entry(row, self.target_var, t, width=50).pack(side="left", fill="x", expand=True)
        if got.kind != "url":
            button(row, "Browse…", self.browse, t).pack(side="left", padx=(6, 0))
        self.target_note = label(body, "", t, font="small", wraplength=520)
        self.target_note.pack(anchor="w")

        # anything worth a second look
        self.warn_frame = tk.Frame(body, bg=t["page"])
        self.warn_frame.pack(fill="x")
        self.trust_var = tk.BooleanVar(value=False)

        label(body, f"These are the sender's drawings, so it may not always recognize the way "
                    "you draw it. Adding a drawing of your own fixes that.", t, muted=True,
              font="small", wraplength=520).pack(anchor="w", pady=(14, 0))
        self.own_var = tk.BooleanVar(value=True)
        _check(body, "Add my own drawing after this", self.own_var, t).pack(anchor="w")

        row = tk.Frame(body, bg=t["page"])
        row.pack(fill="x", pady=(14, 0))
        self.add_btn = button(row, "Add to my book", self.add, t, primary=True)
        self.add_btn.pack(side="right")
        button(row, "Cancel", self.win.destroy, t).pack(side="right", padx=8)
        button(row, "◂ Back", self._ask, t).pack(side="left")

        self.target_var.trace_add("write", lambda *a: self._target_changed())
        self._target_changed()
        _center(self.win, self.book.root)

    def _replace_changed(self) -> None:
        if self.replace_var.get():
            self.name_var.set(self.clash.name)
            self.name_entry.configure(state="disabled")
        else:
            self.name_entry.configure(state="normal")
            self.name_var.set(share.free_name(self.got.name, [s.name for s in store.load()]))

    def browse(self) -> None:
        kind = self.got.kind
        if kind == "folder":
            path = filedialog.askdirectory(parent=self.win, title="Find the folder")
        elif kind == "app":
            path = filedialog.askopenfilename(
                parent=self.win, title="Find the program on your computer",
                filetypes=[("Programs and shortcuts", "*.exe *.lnk *.bat *.cmd *.url"),
                           ("All files", "*.*")])
        else:
            path = filedialog.askopenfilename(parent=self.win, title="Find the file")
        if path:
            self.target_var.set(os.path.normpath(path))

    def _target(self) -> str:
        return actions.normalize_target(self.got.kind, self.target_var.get())

    def _found(self) -> bool:
        target = self._target()
        if not target or (self.got.kind != "url" and share.unresolved(target)):
            return False
        if self.got.kind == "url" or not os.path.isabs(target):
            return True
        return os.path.exists(target)

    def _target_changed(self) -> None:
        t, kind, target = self.t, self.got.kind, self._target()
        if not target:
            self.target_note.configure(text="Fill this in.", fg=t["accent"])
        elif kind == "url":
            self.target_note.configure(text="", fg=t["ink_soft"])
        elif share.unresolved(target):
            self.target_note.configure(
                text="✗ This points to a folder your computer doesn't have. If you have it, "
                     "click Browse… and pick your copy.", fg=t["accent"])
        elif not os.path.isabs(target):
            self.target_note.configure(
                text="Found by name (like notepad.exe). Use “Test it” after adding to check it "
                     "opens.", fg=t["ink_soft"])
        elif os.path.exists(target):
            self.target_note.configure(text="✓ Found on this computer.", fg=t["ink_soft"])
        else:
            what = {"app": "program", "file": "file", "folder": "folder"}[kind]
            self.target_note.configure(
                text=f"✗ Not found on this computer. If you have this {what}, click Browse… "
                     "and pick your copy.", fg=t["accent"])

        for child in self.warn_frame.winfo_children():
            child.destroy()
        notes = share.review(kind, target) if target else []
        if notes:
            box = tk.Frame(self.warn_frame, bg=t["page"], highlightthickness=1,
                           highlightbackground=t["accent"], padx=10, pady=8)
            box.pack(fill="x", pady=(12, 0))
            for note in notes:
                lab = label(box, "⚠  " + note, t, font="small", wraplength=500)
                lab.pack(anchor="w")
            _check(box, "I trust who sent this", self.trust_var, t,
                   command=self._update_add).pack(anchor="w", pady=(6, 0))
        self.notes = notes
        self._update_add()

    def _update_add(self) -> None:
        ok = self._found() and (not self.notes or self.trust_var.get())
        self.add_btn.configure(state="normal" if ok else "disabled")

    def add(self) -> None:
        if str(self.add_btn["state"]) == "disabled":
            return
        name = " ".join(self.name_var.get().split())
        replace = self.replace_var.get()
        sigils = store.load()
        clash = store.find(sigils, name)
        if not name:
            messagebox.showwarning("Receive a sigil", "Give the sigil a name.", parent=self.win)
            return
        if clash and not replace:
            messagebox.showwarning("Receive a sigil",
                                   f"There's already a sigil called “{clash.name}”. Pick another "
                                   "name, or tick “Replace”.", parent=self.win)
            return
        sigil = self.got.to_sigil(name, self._target())
        if clash and replace:
            sigils[sigils.index(clash)] = sigil
        else:
            sigils.append(sigil)
        store.save(sigils)

        book, own = self.book, self.own_var.get()
        self.win.destroy()
        book.selected = sigil.name
        book.refresh()
        book.set_status(f"Received {sigil.name}.")
        if own:
            editor = SigilEditor(book, sigil)
            book.set_status(f"Received {sigil.name}. Draw it your way and click “Add this "
                            "drawing”, then Save.")
            editor.pad.focus_set()
