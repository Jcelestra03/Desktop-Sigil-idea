"""Help for new users: short "?" explanations, and a guided tour of the Sigil Book.

- HELP holds one short explanation per button. A "?" next to a button shows it while the
  mouse is over the "?" (help_mark for dialogs; SigilBook._help on the book canvas).
- Tour walks through the book one part at a time: it outlines the part on the page and
  shows a card next to it. It starts by itself the first time the book opens and can be
  replayed with "✦ Tutorial" at the top of the window.
- The tour ends with an optional practice cast: draw a circle on the dimmed screen. It is
  checked against a few built-in practice shapes, so nothing is saved and nothing opens.
"""

from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from .recognizer import DEFAULT_MIN_SCORE, Stroke, recognize
from .themes import blend

if TYPE_CHECKING:
    from .manager import SigilBook

CAP = 0.7  # cap height as a share of the font size (same as manager.CAP)

# ---- the "?" explanations ---------------------------------------------------------

HELP: dict[str, tuple[str, str]] = {
    # Sigil Book
    "theme": ("Grimoire", "Switch between the Parchment and Obsidian look. Your choice is "
                          "remembered."),
    "index": ("Sigil Index", "All your sigils. Click one to see it on the right page; "
                             "double-click to edit it. Use the arrows or the mouse wheel to "
                             "turn pages."),
    "inscribe": ("Inscribe a new sigil", "Make a new sigil: name it, choose what it opens, "
                                         "and draw it 3 times on the drawing pad."),
    "cast": ("Cast a sigil", "The screen dims. Draw a sigil with the mouse and let go: what "
                             "it's linked to opens. Esc or right-click cancels."),
    "test": ("Test a drawing", "Like casting, but nothing opens. Shows which sigil your "
                               "drawing matched and how closely."),
    "receive": ("Receive a sigil", "Add a sigil a friend sent you, from a .sigil file or a "
                                   "code that starts with SIGIL1-."),
    "hotkey": ("Hotkey", "A keyboard shortcut that starts a cast from anywhere. Click to "
                         "change it, for example if another program already uses it."),
    "orb": ("Floating ✦ button", "A small button that stays on top of your screen. Click it "
                                 "to cast, drag it to move it, right-click it for a menu."),
    "edit": ("Edit", "Change the name, what it opens, the pen, or its drawings."),
    "test_it": ("Test it", "Draw it on the dimmed screen to check it's recognized. Nothing "
                           "opens."),
    "share": ("Share", "Save it as a .sigil file or copy a code to send to a friend."),
    "erase": ("Erase", "Remove this sigil from the book. You'll be asked first."),
    # sigil editor
    "name": ("Name", "What the sigil is called in your index, for example “Steam”."),
    "kind": ("What it opens", "Program: an app or game (.exe or a shortcut). Website: a web "
                              "address. File: any document. Folder: opens in File Explorer."),
    "target": ("Where it points", "Click Browse… to pick it, or type it in. For a website, "
                                  "just type the address, like canvas.uw.edu."),
    "drawings": ("Your drawings", "The shapes the book learns from. Draw it the same way 3 "
                                  "times. Click a drawing to remove it."),
    "pen": ("Pen", "How your lines look: Pen, Brush, Calligraphy, Quill, Marker, Spray or "
                   "Glow. Only the look changes; recognition stays the same."),
    "size": ("Size", "How thick the lines are."),
    "color": ("Ink color", "✦ is the grimoire's own ink. More… lets you pick any color."),
    "clear": ("Clear", "Wipe the drawing pad."),
    "undo": ("Undo", "Remove the last stroke (Ctrl+Z)."),
    "add": ("Add this drawing", "Keep the drawing on the pad as one of the sigil's drawings."),
    "save": ("Save sigil", "Write it into the book. It can be cast right away."),
}


# ---- tooltips --------------------------------------------------------------------

_tip: list[tk.Toplevel | None] = [None]


def hide_tip() -> None:
    win, _tip[0] = _tip[0], None
    if win is not None:
        try:
            win.destroy()
        except tk.TclError:
            pass


def show_tip(master: tk.Misc, x: float, y: float, key: str, t: dict) -> None:
    """Show HELP[key] in a small themed card just below screen point (x, y)."""
    hide_tip()
    title, text = HELP[key]
    win = tk.Toplevel(master, bg=t["gilt"])
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    box = tk.Frame(win, bg=t["field"], padx=12, pady=8)
    box.pack(padx=2, pady=2)
    tk.Label(box, text=title, bg=t["field"], fg=t["accent"], font=t["font_button"],
             anchor="w").pack(anchor="w")
    tk.Label(box, text=text, bg=t["field"], fg=t["ink"], font=t["font_small"], anchor="w",
             justify="left", wraplength=280).pack(anchor="w", pady=(2, 0))
    win.update_idletasks()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    left = int(min(max(4, x - w / 2), sw - w - 4))
    top = int(y + 10 if y + 10 + h < sh - 48 else y - h - 30)
    win.geometry(f"+{left}+{top}")
    _tip[0] = win


def help_mark(parent: tk.Misc, key: str, t: dict) -> tk.Canvas:
    """A small circled "?" for dialogs. Hover (or click) it to see HELP[key]."""
    size = 18
    bg = parent.cget("bg")
    mark = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0,
                     cursor="question_arrow")
    ring = mark.create_oval(2, 2, size - 2, size - 2, outline=t["ink_soft"])
    q = mark.create_text(size / 2, size / 2, text="?", fill=t["ink_soft"],
                         font=(t["font_small"][0], 9, "bold"))

    def enter(_=None):
        mark.itemconfigure(ring, outline=t["accent"])
        mark.itemconfigure(q, fill=t["accent"])
        show_tip(mark, mark.winfo_rootx() + size / 2, mark.winfo_rooty() + size, key, t)

    def leave(_=None):
        mark.itemconfigure(ring, outline=t["ink_soft"])
        mark.itemconfigure(q, fill=t["ink_soft"])
        hide_tip()

    mark.bind("<Enter>", enter)
    mark.bind("<Leave>", leave)
    mark.bind("<Button-1>", enter)
    mark.bind("<Destroy>", lambda e: hide_tip() if e.widget is mark else None)
    return mark


# ---- practice shapes ---------------------------------------------------------------

@dataclass
class PracticeShape:
    name: str
    templates: list[list[Stroke]]


def _poly(points, steps=16) -> Stroke:
    out: Stroke = []
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        out.extend((ax + (bx - ax) * i / steps, ay + (by - ay) * i / steps) for i in range(steps))
    out.append(points[-1])
    return out


def _circle(squash=1.0) -> list[Stroke]:
    return [[(100 + 80 * math.cos(a / 40 * 2 * math.pi),
              100 + 80 * squash * math.sin(a / 40 * 2 * math.pi)) for a in range(41)]]


PRACTICE_TARGET = "circle"
PRACTICE_SHAPES = [
    PracticeShape("circle", [_circle(), _circle(0.8)]),
    PracticeShape("triangle", [[_poly([(100, 20), (180, 170), (20, 170), (100, 20)])]]),
    PracticeShape("cross", [[_poly([(20, 20), (180, 180)]), _poly([(180, 20), (20, 180)])]]),
    PracticeShape("lightning bolt", [[_poly([(120, 10), (60, 100), (140, 100), (80, 190)])]]),
    PracticeShape("line", [[_poly([(20, 100), (180, 100)])]]),
]


def check_practice(strokes: list[Stroke]) -> tuple[str | None, float]:
    """Which practice shape the drawing looks like, and the score (None if none)."""
    match = recognize(strokes, PRACTICE_SHAPES, min_score=DEFAULT_MIN_SCORE)
    return (match.sigil.name, match.score) if match else (None, 0.0)


# ---- the guided tour ---------------------------------------------------------------

@dataclass
class Step:
    region: str | None   # a key of SigilBook.regions to outline, or None for a centered card
    title: str
    text: str


STEPS = [
    Step(None, "Welcome to your Sigil Book",
         "Here you inscribe sigils: symbols that open a program, game, website, file or "
         "folder when you draw them on your screen.\n\nWant a quick tour? It takes about a "
         "minute, and you can stop at any time."),
    Step("theme", "Choose your grimoire",
         "Switch between the Parchment and Obsidian book here. Your choice is remembered."),
    Step("index", "The Sigil Index",
         "Every sigil you inscribe is listed on this page. Click one to see it on the right "
         "page, with Edit, Test it, Share and Erase. Double-click to edit it."),
    Step("inscribe", "Inscribe a new sigil",
         "Name it, choose what it opens (a program, website, file or folder), then draw it "
         "3 times the same way on the drawing pad. Pick any pen, size and ink you like: "
         "the pen only changes the look."),
    Step("cast", "Cast a sigil",
         "The screen dims. Draw your sigil with the mouse and let go; a moment later it "
         "opens. You can also click the floating ✦ button or press {hotkey}. Esc or "
         "right-click cancels."),
    Step("test", "Test a drawing",
         "Like casting, but nothing opens. It tells you which sigil your drawing matched "
         "and how closely: handy for practice."),
    Step("receive", "Share and receive",
         "Got a sigil from a friend? Receive it here, from a .sigil file or a code. To send "
         "one of yours, pick it in the index and choose Share."),
    Step("switches", "Hotkey and floating button",
         "Click the hotkey to change the shortcut. Turn the floating ✦ button on or off; "
         "you can drag it anywhere on your screen."),
    Step("cast", "Try it out (optional)",
         "Practice a cast. Nothing opens and nothing is saved.\n\nClick Practice, then "
         "draw a circle anywhere on the dimmed screen and let go."),
    Step("tutorial", "You're ready",
         "Hover over any ? to get a quick reminder of what a button does. Choose "
         "“✦ Tutorial” at the top to see this tour again."),
]
PRACTICE_STEP = 8


class Tour:
    """The guided tour, drawn on the book canvas (items tagged "tour")."""

    def __init__(self, book: SigilBook) -> None:
        self.book = book
        self.i = 0
        self.result = ""        # what the last practice cast said
        self.practiced = False  # a practice cast succeeded

    # ---- moving through the steps ----

    def go(self, i: int) -> None:
        self.i = max(0, min(len(STEPS) - 1, i))
        self.book.draw_pages()

    def end(self) -> None:
        self.book.canvas.delete("tour")
        self.book.tour = None
        self.book.draw_pages()

    def inscribe(self) -> None:
        self.end()
        self.book.new_sigil()

    def practice(self) -> None:
        def done(strokes: list[Stroke] | None) -> str | None:
            if strokes is None:
                self.result = "Cancelled. Click Practice to try again."
                message = None
            else:
                name, score = check_practice(strokes)
                if name == PRACTICE_TARGET:
                    self.practiced = True
                    self.result = (f"✦ Well cast! That's a circle ({score:.0%} match). With a "
                                   "real sigil, its program or website would open now.")
                    message = f"✦ Circle  ·  {score:.0%} match"
                elif name:
                    self.result = f"That looked more like a {name}. Try again, a bit rounder."
                    message = f"That looked like a {name}"
                else:
                    self.result = "The book couldn't read that one. Try a bigger, rounder circle."
                    message = "Not recognized"
            if self.book.tour is self:
                self.book.draw_pages()
            return message

        self.book.app.practice("Practice: draw a circle", done)

    # ---- drawing ----

    def _buttons(self) -> tuple[list, list]:
        """(left, right) buttons of the card: (text, command, primary)."""
        i, last = self.i, len(STEPS) - 1
        back = ("◂ Back", lambda: self.go(i - 1), False)
        if i == 0:
            return [("Not now", self.end, False)], [("Show me around ▸", lambda: self.go(1), True)]
        if i == PRACTICE_STEP:
            label = "✦ Try again" if self.result else "✦ Practice"
            return [back], [("Skip" if not self.practiced else "Next ▸", lambda: self.go(i + 1),
                             False), (label, self.practice, True)]
        if i == last:
            if not self.book.sigils:
                return [back], [("Finish", self.end, False),
                                ("✒ Inscribe my first sigil", self.inscribe, True)]
            return [back], [("Finish", self.end, True)]
        return [back, ("Skip tour", self.end, False)], [("Next ▸", lambda: self.go(i + 1), True)]

    def draw(self) -> None:
        b, c = self.book, self.book.canvas
        c.delete("tour")
        if not hasattr(b, "layout"):
            return
        step = STEPS[self.i]
        box = b.regions.get(step.region) if step.region else None

        before, hits = set(c.find_all()), len(b.hits)
        if box:
            self._outline(box)
        lay = b.layout
        page_w = lay.right[2] - lay.right[0]
        w = min(420, page_w - 40)
        if box is None:
            cx = lay.gutter
        elif (box[0] + box[2]) / 2 < lay.gutter:
            cx = (lay.right[0] + lay.right[2]) / 2
        else:
            cx = (lay.left[0] + lay.left[2]) / 2
        top_min, bottom_max = lay.book[1] + 14, lay.book[3] - 14

        mark = set(c.find_all())
        h = self._card(cx - w / 2, top_min, w, hits)
        if box is None:
            top = (lay.book[1] + lay.book[3] - h) / 2
        else:
            top = min(max((box[1] + box[3] - h) / 2, top_min), bottom_max - h)
        if abs(top - top_min) > 1:   # draw it again where it belongs
            c.delete(*(set(c.find_all()) - mark))
            del b.hits[hits:]
            self._card(cx - w / 2, top, w, hits)

        for item in set(c.find_all()) - before:
            c.addtag_withtag("tour", item)
        c.tag_raise("tour")

    def _outline(self, box) -> None:
        t, c = self.book.theme, self.book.canvas
        x0, y0, x1, y1 = box
        c.create_rectangle(x0 - 9, y0 - 7, x1 + 9, y1 + 7, outline=blend(t["accent"], t["page"], .55),
                           width=5)
        c.create_rectangle(x0 - 6, y0 - 4, x1 + 6, y1 + 4, outline=t["accent"], width=2)

    def _card(self, x0: float, top: float, w: float, hits: int) -> float:
        """Draw the card with its top-left at (x0, top); returns its height."""
        b, c, t = self.book, self.book.canvas, self.book.theme
        eb, eh, ebtn = b._em("body"), b._em("head"), b._em("button")
        pad = 1.3 * eb
        x1 = x0 + w
        first = None
        y = top + pad

        last = len(STEPS) - 1
        if 0 < self.i < last:
            first = b._write(x0 + pad, y + CAP * b._em("italic"), f"{self.i} of {last - 1}",
                             "italic", t["ink_soft"], anchor="w")
            y += CAP * b._em("italic") + 0.5 * eb
        item = b._write(x0 + pad, y + CAP * eh, b._fit(STEPS[self.i].title, "head", w - 2 * pad),
                        "head", t["accent"], anchor="w")
        first = first or item
        y += CAP * eh + 0.9 * eb

        hotkey = b.hotkey_text.split(" · ")[0].replace("Hotkey: ", "") if b.app.hotkey else ""
        text = STEPS[self.i].text.format(hotkey=hotkey or "your hotkey")
        body = c.create_text(x0 + pad, y, text=text, width=w - 2 * pad, anchor="nw",
                             font=b._font("body"), fill=t["ink"], justify="left")
        y = c.bbox(body)[3]
        if self.i == PRACTICE_STEP and self.result:
            res = c.create_text(x0 + pad, y + 0.7 * eb, text=self.result, width=w - 2 * pad,
                                anchor="nw", font=b._font("italic"),
                                fill=t["accent"] if self.practiced else t["ink_soft"])
            y = c.bbox(res)[3]

        base = y + 1.1 * eb + CAP * ebtn
        left, right = self._buttons()
        x = x0 + pad
        for text, command, primary in left:
            bx = b._button(x, base, text, command, anchor="w",
                           color=t["accent"] if primary else t["ink_soft"])
            x = bx[2] + 0.8 * eb
        x = x1 - pad
        for text, command, primary in reversed(right):
            bx = b._button(x, base, text, command, anchor="e",
                           color=t["accent"] if primary else t["ink_soft"])
            x = bx[0] - 0.8 * eb
        bottom = base + 0.35 * ebtn + pad * 0.8

        shadow = c.create_rectangle(x0 + 5, top + 6, x1 + 5, bottom + 6,
                                    fill=blend(t["page_dark"], t["desk"], .3), outline="")
        card = c.create_rectangle(x0, top, x1, bottom, fill=t["field"], outline=t["gilt"], width=3)
        inner = c.create_rectangle(x0 + 6, top + 6, x1 - 6, bottom - 6, outline=t["field_line"])
        c.tag_lower(inner, first)
        c.tag_lower(card, inner)
        c.tag_lower(shadow, card)
        # clicks on the card don't reach the page underneath (button hits come after this)
        from .manager import Hit
        b.hits.insert(hits, Hit((x0, top, x1, bottom), lambda: None, pointer=False))
        return bottom - top
