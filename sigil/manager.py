"""Sigil Book: the main window, drawn as an open grimoire. Add, edit, test and cast sigils
without the terminal.

Left page: the Sigil Index (click a sigil to select it, double-click to edit, ◂ ▸ to turn
pages). Right page: the selected sigil's seal and the actions. Two looks, chosen at the
top of the window: Parchment and Obsidian (see themes.py).

While this window is open (or minimized), the hotkey and the floating cast button work.
"""

from __future__ import annotations

import math
import os
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from tkinter import colorchooser, filedialog, messagebox, simpledialog
from typing import Callable

from . import actions, grimoire, store, themes, tutorial
from .app import SigilApp
from .drawpad import DEFAULT_STYLE, MAX_SIZE, MIN_SIZE, PENS, DrawPad, draw_strokes, render_stroke
from .hotkey import parse as parse_hotkey, pretty
from .overlay import make_root
from .recognizer import DEFAULT_MIN_SCORE, Stroke, compare, recognize
from .themes import blend

RECOMMENDED_SAMPLES = 3
CAP = 0.7  # cap height as a share of the font size, for placing text by its baseline

# ink colors in the editor, after the grimoire's own ink (black, crimson, gold, amethyst,
# sapphire, emerald, amber, rose, teal, white, brown)
PALETTE = ["#1b1b1b", "#a32a1e", "#e0c27a", "#6b3f8f", "#2f5fa8", "#2f7d4f", "#d9772b",
           "#c8487a", "#4fb3bf", "#ffffff", "#7a5230"]

TARGET_LABELS = {
    "app": "Program to open",
    "url": "Web address",
    "file": "File to open",
    "folder": "Folder to open",
}

OPENS = {"app": "Opens the program", "url": "Opens the website", "file": "Opens the file",
         "folder": "Opens the folder"}


@dataclass
class Hit:
    """A clickable spot on the book canvas."""
    box: tuple[float, float, float, float]
    on_click: Callable[[], None]
    on_double: Callable[[], None] | None = None
    item: int | None = None
    color: str = ""
    hover: str = ""
    tip: str = ""         # a tutorial.HELP key: hovering shows that explanation
    pointer: bool = True  # show the hand cursor


class SigilBook:
    def __init__(self) -> None:
        root = self.root = make_root()
        root.title("Desktop Sigil — Sigil Book")
        root.geometry("1160x760")
        root.minsize(1000, 680)
        icon = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "assets", "sigil.ico")
        if os.path.exists(icon):  # the seal icon, for this window and every dialog
            root.iconbitmap(default=icon)
        root.protocol("WM_DELETE_WINDOW", self.quit)

        self.settings = store.load_settings()
        self.theme = themes.get(self.settings.get("theme"))
        self.app = SigilApp(root, on_status=self.set_status)
        self.orb: CastOrb | None = None
        self.sigils: list[store.Sigil] = []
        self.selected: str | None = None
        self.folio = 0
        self.status = "Ready."
        self.hotkey_text = ""
        self.hits: list[Hit] = []
        self._hover: Hit | None = None
        self._size = (0, 0)
        self._resize_job: str | None = None
        self._fonts: dict[str, tkfont.Font] = {}
        self._scale = 1.0
        self.regions: dict[str, tuple[float, float, float, float]] = {}  # for the tour
        self.tour: tutorial.Tour | None = None

        self.canvas = tk.Canvas(root, highlightthickness=0, bg=self.theme["desk"])
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", lambda e: self._set_hover(None))
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Double-Button-1>", self._on_double)
        self.canvas.bind("<MouseWheel>", self._on_wheel)

        self.sigils = store.load()
        self.apply_hotkey(self.settings["hotkey"], initial=True)
        if self.settings["orb"]:
            self.show_orb()
        root.deiconify()
        if not self.settings.get("tutorial_seen"):
            root.after(500, self.start_tour)

    # ---- drawing ------------------------------------------------------------

    # Resizing: Tk repaints every canvas item for every step of a window drag, and the
    # grimoire has about 1,500 small ones (rune writing, fur strands), ~180 ms a frame.
    # So while the size is changing, those "detail" items are hidden (~40 ms a frame),
    # and the book is drawn once at the new size when the mouse stops.
    RESIZE_SETTLE_MS = 150

    def _on_resize(self, event: tk.Event) -> None:
        if (event.width, event.height) == self._size:
            return
        self._size = (event.width, event.height)
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        else:
            self.canvas.itemconfigure("detail", state="hidden")
        self._resize_job = self.root.after(self.RESIZE_SETTLE_MS, self.redraw)

    def redraw(self) -> None:
        """Repaint everything: the grimoire background and the page contents."""
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = None
        c = self.canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 1000), max(c.winfo_height(), 680)
        self.layout = grimoire.draw(c, w, h, self.theme)
        for item in c.find_all():
            c.addtag_withtag("bg", item)
            if c.type(item) in ("text", "line"):
                c.addtag_withtag("detail", item)
        self._fit_type()
        self.draw_pages()

    def draw_pages(self) -> None:
        """Repaint only the writing on the pages (fast; used on every click)."""
        c = self.canvas
        c.delete("fg")
        self.hits = []
        self._set_hover(None)
        self.regions = {"index": self.layout.left}
        self._draw_theme_switch()
        self._draw_index(self.layout.left)
        self._draw_right(self.layout.right)
        for item in c.find_all():
            if not c.gettags(item):
                c.addtag_withtag("fg", item)
        c.tag_raise("front")
        if self.tour:
            self.tour.draw()

    # ---- type ---------------------------------------------------------------
    # Text is placed by its baseline and spaced in ems (the font size in pixels) instead of
    # fixed pixel offsets. That keeps the gaps even at any window size, at Windows display
    # scaling (125 %, 150 %…), and with Gabriola, whose line box is much taller than its
    # letters. The type itself grows a little on big windows and shrinks on small ones.

    def _font(self, name: str) -> tkfont.Font:
        f = self._fonts.get(name)
        if f is None:
            family, size, *style = self.theme[f"font_{name}"]
            size = round(size * self._scale) if size > 0 else -round(-size * self._scale)
            f = self._fonts[name] = tkfont.Font(root=self.root, family=family, size=size,
                                                slant="italic" if "italic" in style else "roman")
        return f

    def _em(self, name: str) -> float:
        size = self._font(name).actual("size")
        return -size if size < 0 else size * self.root.winfo_fpixels("1p")

    def _set_scale(self, scale: float) -> None:
        self._scale = scale
        self._fonts = {}

    def _fit_type(self) -> None:
        """Pick the type scale so the right page (the fullest one) fits the page height."""
        self._set_scale(1.0)
        x0, y0, x1, y1 = self.layout.right
        fit = (y1 - y0) / self._right_need()
        scale = fit if fit < 1 else min(1.25, 1 + (fit - 1) * 0.4)
        self._set_scale(max(0.7, scale))

    def _text(self, x, y, text, font, color=None, **kw) -> int:
        return self.canvas.create_text(x, y, text=text, font=self._font(font),
                                       fill=color or self.theme["ink"], **kw)

    def _write(self, x, base, text, font, color=None, anchor="center", **kw) -> int:
        """Text whose first baseline sits at `base`; anchor is "w", "center" or "e"."""
        y = base - self._font(font).metrics("ascent")
        return self._text(x, y, text, font, color, anchor={"w": "nw", "center": "n", "e": "ne"}[anchor],
                          **kw)

    def _button(self, x, base, text, command, font="button", anchor="center", color=None,
                hover=None, on_double=None) -> tuple[float, float, float, float]:
        t = self.theme
        color = color or t["ink"]
        item = self._write(x, base, text, font, color, anchor=anchor)
        x0, y0, x1, y1 = self.canvas.bbox(item)
        box = (x0 - 6, y0 - 3, x1 + 6, y1 + 3)
        self.hits.append(Hit(box, command, on_double, item, color, hover or t["accent"]))
        return box

    def _help(self, box, key: str, x: float | None = None, y: float | None = None) -> None:
        """A small circled "?" at the top right of a button's box (or at x, y); hovering it
        shows tutorial.HELP[key]."""
        t, c = self.theme, self.canvas
        r = max(6.0, 0.55 * self._em("small"))
        cx = (box[2] if x is None else x) + r
        cy = (box[1] if y is None else y) + r
        color = t["ink_soft"]
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color)
        item = c.create_text(cx, cy, text="?", fill=color,
                             font=(t["font_small"][0], -round(r * 1.35), "bold"))
        hit = Hit((cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2), lambda: None, None, item,
                  color, t["accent"], tip=key)
        hit.on_click = lambda: self._show_tip(hit)
        self.hits.append(hit)

    def _show_tip(self, hit: Hit) -> None:
        x0, _, x1, y1 = hit.box
        c = self.canvas
        tutorial.show_tip(c, c.winfo_rootx() + (x0 + x1) / 2, c.winfo_rooty() + y1, hit.tip,
                          self.theme)

    def _line(self, cx, text, font, color=None) -> tuple[float, Callable[[float], None]]:
        """A part for _stack: centered text, measured from cap height to the last baseline."""
        em = self._em(font)
        h = CAP * em + text.count("\n") * self._font(font).metrics("linespace")
        return h, lambda y: self._write(cx, y + CAP * em, text, font, color, justify="center")

    @staticmethod
    def _stack(top, bottom, parts) -> None:
        """Draw parts top to bottom as one block, centered between top and bottom.
        A part is a gap (a number) or a (height, draw(y_top)) pair."""
        total = sum(p if isinstance(p, (int, float)) else p[0] for p in parts)
        y = top + max(0.0, (bottom - top - total) / 2)
        for p in parts:
            if isinstance(p, (int, float)):
                y += p
            else:
                p[1](y)
                y += p[0]

    def _fit(self, text: str, font: str, width: float) -> str:
        f = self._font(font)
        if f.measure(text) <= width:
            return text
        while text and f.measure(text + "…") > width:
            text = text[:-1]
        return text + "…"

    # ---- shared page parts ----------------------------------------------------

    def _divider(self, cx, y, half) -> None:
        t = self.theme
        gap = self._em("small") * 1.2
        self.canvas.create_line(cx - half, y, cx - gap, y, fill=t["ink_soft"])
        self.canvas.create_line(cx + gap, y, cx + half, y, fill=t["ink_soft"])
        self._text(cx, y, "✦", "small", t["accent"])

    def _header_height(self) -> float:
        et = self._em("title")
        return 6 + CAP * et + 0.5 * et + 0.9 * self._em("body")

    def _header(self, rect, title: str, help_key: str | None = None) -> float:
        """Page title and ✦ divider, at the same height on both pages. Returns where the
        page body starts."""
        x0, y0, x1, y1 = rect
        cx, et = (x0 + x1) / 2, self._em("title")
        base = y0 + 6 + CAP * et
        item = self._write(cx, base, self._fit(title, "title", x1 - x0), "title")
        if help_key:
            # Gabriola's line box is much taller than its letters: sit at the cap height
            self._help(self.canvas.bbox(item), help_key, y=base - CAP * et - 2)
        self._divider(cx, base + 0.5 * et, (x1 - x0) / 2 - 20)
        return y0 + self._header_height()

    def _footer(self, rect) -> float:
        """Baseline of the last line on both pages (folio on the left, status on the right)."""
        return rect[3] - 6

    def _seal(self, cx, cy, r, strokes: list[Stroke] | None, width=3, runes=True,
              style: dict | None = None) -> None:
        """A double ink ring with runes between the rings, like the seals in the pictures."""
        t, c = self.theme, self.canvas
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=t["accent"], width=width)
        inner = r - (12 if runes else 5)
        c.create_oval(cx - inner, cy - inner, cx + inner, cy + inner, outline=t["accent"], width=1)
        if runes:
            for i, ch in enumerate(grimoire.RUNES[:16]):
                a = i / 16 * 2 * math.pi - math.pi / 2
                c.create_text(cx + math.cos(a) * (r - 6), cy + math.sin(a) * (r - 6), text=ch,
                              fill=t["accent"], font=("Segoe UI Historic", max(7, int(r / 11))))
        box = inner * 0.68
        if strokes:
            draw_strokes(c, strokes, cx - box, cy - box, box * 2, box * 2, t["accent"], width,
                         style=style or None, bg=t["page"])
        elif strokes is None:
            c.create_text(cx, cy, text="✦", fill=t["accent"], font=("Segoe UI Symbol", int(r * .7)))

    def _draw_theme_switch(self) -> None:
        """"Grimoire: Parchment Obsidian", centered over the spine in the band above the book."""
        t = self.theme
        eb = self._em("body")
        base = self.layout.book[1] / 2 + CAP * eb / 2
        gap = 1.6 * eb
        label = "Grimoire:"
        choices = list(themes.THEMES.values())
        widths = [self._font("body").measure(c["label"]) for c in choices]
        label_w = self._font("small").measure(label)
        # then a "?", a dot, and the tutorial (here, because props cover the band's corners)
        tutorial_text = "✦ Tutorial"
        tail = 1.7 * gap + self._font("body").measure(tutorial_text)
        x = self.layout.gutter - (label_w + 0.6 * gap + sum(widths) + gap * (len(choices) - 1)
                                  + tail) / 2
        first = self.canvas.bbox(self._write(x, base, label, "small", t["desk_text"], anchor="w"))
        x += label_w + 0.6 * gap
        for theme, w in zip(choices, widths):
            box = self._button(x, base, theme["label"], lambda n=theme["name"]: self.set_theme(n),
                               font="body", anchor="w", color=t["desk_text"])
            if theme["name"] == t["name"]:
                uy = base + 0.4 * eb
                self.canvas.create_line(x, uy, x + w, uy, fill=t["accent"], width=2)
            x += w + gap
        self.regions["theme"] = (first[0], box[1], box[2], box[3])
        self._help(box, "theme")
        x = box[2] + gap
        self._write(x, base, "·", "body", t["desk_text"])
        self.regions["tutorial"] = self._button(x + 0.7 * gap, base, tutorial_text,
                                                self.start_tour, "body", anchor="w",
                                                color=t["desk_text"])

    # ---- left page: the index ------------------------------------------------

    def _row(self) -> tuple[float, float]:
        """Seal radius and row height of the index."""
        en = self._em("name")
        r = round(1.05 * en)
        return r, 2 * r + round(0.55 * en)

    def _draw_index(self, rect) -> None:
        t, c = self.theme, self.canvas
        x0, y0, x1, y1 = rect
        cx = (x0 + x1) / 2
        top = self._header(rect, "Sigil Index", "index")
        foot = self._footer(rect)
        bottom = foot - 1.8 * self._em("small")

        r, row_h = self._row()
        per_page = max(1, int((bottom - top) // row_h))
        pages = max(1, math.ceil(len(self.sigils) / per_page))
        self.folio = min(self.folio, pages - 1)
        shown = self.sigils[self.folio * per_page:(self.folio + 1) * per_page]

        if not self.sigils:
            self._stack(top, bottom, [
                self._line(cx, "No sigils inscribed yet.", "head"),
                1.1 * self._em("body"),
                self._line(cx, "Choose “Inscribe a new sigil” on the right page,\n"
                               "pick what it opens, and draw its shape. Or choose\n"
                               "“Receive a sigil” to add one a friend sent you.", "body",
                           t["ink_soft"]),
            ])
            return

        en, es = self._em("name"), self._em("small")
        gap = 0.45 * en
        block = CAP * en + gap + CAP * es        # name + detail, cap top to last baseline
        tx = x0 + 2 * r + 0.6 * en
        room = x1 - tx
        inset = max(2, row_h * 0.04)
        for i, sigil in enumerate(shown):
            ry = top + i * row_h
            cy = ry + row_h / 2
            band = (x0 - 10, ry + inset, x1 + 10, ry + row_h - inset)
            if sigil.name == self.selected:
                c.create_rectangle(*band, fill=blend(t["page"], t["page_dark"], .35), outline="")
                c.create_line(band[0], band[1], band[0], band[3], fill=t["accent"], width=3)
            self._seal(x0 + r + 2, cy, r, sigil.templates[0] if sigil.templates else [],
                       width=2, runes=False, style=sigil.style)
            name_base = cy - block / 2 + CAP * en
            self._write(tx, name_base, self._fit(sigil.name, "name", room), "name", anchor="w")
            kind = actions.KINDS.get(sigil.action["type"], sigil.action["type"])
            detail = self._fit(f"{kind} · {sigil.action['target']}", "small", room)
            self._write(tx, name_base + gap + CAP * es, detail, "small", t["ink_soft"], anchor="w")
            self.hits.append(Hit(band, lambda s=sigil: self.select(s.name),
                                 lambda s=sigil: self.edit(s)))

        self._write(cx, foot, f"folio {self.folio + 1} of {pages}", "italic", t["ink_soft"])
        if self.folio > 0:
            self._button(x0, foot, "◂ turn back", lambda: self.turn(-1), "small", anchor="w")
        if self.folio < pages - 1:
            self._button(x1, foot, "turn page ▸", lambda: self.turn(1), "small", anchor="e")

    # ---- right page: the selected sigil and the actions -------------------------

    def _right_spacing(self) -> dict[str, float]:
        """Vertical rhythm of the right page, in pixels for the current type scale."""
        es, eb = self._em("small"), self._em("button")
        return {
            "pitch": 2.0 * eb,          # between the three action lines
            "to_hotkey": 2.4 * eb,      # last action -> hotkey line
            "hotkey_line": 1.9 * es,    # between the two hotkey lines when they wrap
            "to_status": 2.0 * es,      # hotkey line -> status line
            "divider": CAP * eb + 1.1 * eb,  # divider -> first action's baseline
            "body_gap": 1.4 * eb,       # body content -> divider
            "min_seal": 3.4 * eb,
        }

    def _details(self, cx, width, sigil) -> list:
        """Stack parts under the seal."""
        t, eb = self.theme, self._em("button")
        if not sigil:
            return [0.9 * eb,
                    self._line(cx, "Draw a sigil to open a program, website,\nfile or folder. "
                                   "Pick one from the index to see it here.", "body", t["ink_soft"])]
        n = len(sigil.templates)
        row = [("Edit", lambda: self.edit(sigil), None, "edit"),
               ("Test it", lambda: self.app.summon(dry_run=True), None, "test_it"),
               ("Share", lambda: self.share(sigil), None, "share"),
               ("Erase", lambda: self.delete(sigil), t["accent"], "erase")]
        spread = min(5.2 * eb, width / len(row))

        def buttons(y):
            base = y + CAP * eb
            for i, (text, command, color, key) in enumerate(row):
                box = self._button(cx + (i - (len(row) - 1) / 2) * spread, base, text, command,
                                   color=color)
                self._help(box, key)

        return [0.9 * eb,
                self._line(cx, OPENS.get(sigil.action["type"], "Opens"), "small", t["ink_soft"]),
                0.6 * eb,
                self._line(cx, self._fit(sigil.action["target"], "body", width), "body"),
                0.6 * eb,
                self._line(cx, f"{n} drawing{'s' if n != 1 else ''}", "italic", t["ink_soft"]),
                1.4 * eb,
                (CAP * eb, buttons)]

    def _action_lines(self) -> list[tuple[str, Callable[[], None], str | None, str | None, str]]:
        """(text, command, color, hover color, tutorial key) of the right page's actions."""
        t = self.theme
        return [("✒  Inscribe a new sigil", self.new_sigil, t["accent"], t["ink"], "inscribe"),
                ("✦  Cast a sigil", lambda: self.app.summon(), None, None, "cast"),
                ("◉  Test a drawing", lambda: self.app.summon(dry_run=True), None, None, "test"),
                ("✉  Receive a sigil", self.receive, None, None, "receive")]

    def _right_need(self) -> float:
        """Height the right page needs with the current type, with the smallest seal."""
        s = self._right_spacing()
        x0, y0, x1, y1 = self.layout.right
        fake = store.Sigil("x", {"type": "app", "target": "x"}, [])
        details = sum(p if isinstance(p, (int, float)) else p[0]
                      for p in self._details(0, x1 - x0, fake))
        actions_h = (6 + s["to_status"] + s["to_hotkey"]
                     + (len(self._action_lines()) - 1) * s["pitch"] + s["divider"]
                     + s["body_gap"])
        if not self._switches_fit(x1 - x0):
            actions_h += s["hotkey_line"]
        return self._header_height() + 2 * s["min_seal"] + details + actions_h + 12

    def _switches(self) -> list[tuple[str, Callable[[], None]]]:
        orb = f"Floating ✦ button: {'on' if self.settings['orb'] else 'off'}"
        return [(self.hotkey_text, self.change_hotkey, "hotkey"), (orb, self.toggle_orb, "orb")]

    def _switches_fit(self, width: float) -> bool:
        """Whether the hotkey and floating-button switches fit side by side."""
        small = self._font("small")
        # each switch is followed by a "?" (about 1.4 em)
        return (sum(small.measure(text) for text, *_ in self._switches())
                + 5 * self._em("small")) <= width

    def _status_room(self) -> float:
        x0, _, x1, _ = self.layout.right
        # the Obsidian quill lies across the bottom-right corner of the page
        return (x1 - x0) - (90 if self.theme["name"] == "obsidian" else 10)

    def _draw_right(self, rect) -> None:
        t = self.theme
        x0, y0, x1, y1 = rect
        cx, width = (x0 + x1) / 2, x1 - x0
        s = self._right_spacing()
        sigil = store.find(self.sigils, self.selected) if self.selected else None
        top = self._header(rect, sigil.name if sigil else "Desktop Sigil")

        # bottom up: status, hotkey + floating button, the three actions, divider
        foot = self._footer(rect)
        self.status_item = self._write(cx, foot, self._fit(self.status, "italic", self._status_room()),
                                       "italic", t["ink_soft"])
        switches = self._switches()
        es = self._em("small")
        widths = [self._font("small").measure(text) + 1.4 * es for text, *_ in switches]
        gap = 2 * es
        hot = foot - s["to_status"]
        boxes = []
        if self._switches_fit(width):       # one line, centered as a pair
            x = cx - (sum(widths) + gap) / 2
            for (text, command, key), w in zip(switches, widths):
                boxes.append(self._button(x, hot, text, command, "small", anchor="w",
                                          color=t["ink_soft"]))
                self._help(boxes[-1], key)
                x += w + gap
            hot_top = hot
        else:                               # too narrow: one per line
            for i, (text, command, key) in enumerate(switches):
                boxes.append(self._button(cx, hot - (1 - i) * s["hotkey_line"],
                                          self._fit(text, "small", width - 3 * es), command,
                                          "small", color=t["ink_soft"]))
                self._help(boxes[-1], key)
            hot_top = hot - s["hotkey_line"]
        self.regions["switches"] = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                                    max(b[2] for b in boxes) + 1.4 * es, max(b[3] for b in boxes))

        lines = self._action_lines()
        first = hot_top - s["to_hotkey"] - (len(lines) - 1) * s["pitch"]
        # a left-aligned list (so the icons line up), centered on the page as a block
        longest = max(self._font("button").measure(text) for text, *_ in lines)
        ax = cx - longest / 2
        for i, (text, command, color, hover, key) in enumerate(lines):
            box = self._button(ax, first + i * s["pitch"], text, command, anchor="w", color=color,
                               hover=hover)
            self.regions[key] = box
            self._help(box, key, x=ax + longest + 6)  # the "?"s line up in a column
        divider = first - s["divider"]
        self._divider(cx, divider, width / 2 - 20)

        # the seal and its details, centered in the space that is left
        details = self._details(cx, width, sigil)
        bottom = divider - s["body_gap"]
        fixed = sum(p if isinstance(p, (int, float)) else p[0] for p in details)
        r = max(s["min_seal"] * 0.75, min((bottom - top - fixed) / 2, width / 2 - 10, 150))
        seal = (2 * r, lambda y: self._seal(cx, y + r, r, sigil.templates[0] if sigil and
                                            sigil.templates else (None if not sigil else []),
                                            style=sigil.style if sigil else None,
                                            runes=r >= 48))
        self._stack(top, bottom, [seal, *details])

    # ---- mouse --------------------------------------------------------------

    def _hit_at(self, x, y) -> Hit | None:
        for hit in reversed(self.hits):
            x0, y0, x1, y1 = hit.box
            if x0 <= x <= x1 and y0 <= y <= y1:
                return hit
        return None

    def _set_hover(self, hit: Hit | None) -> None:
        if hit is self._hover:
            return
        old = self._hover
        if old and old.item and self.canvas.find_withtag(old.item):
            self.canvas.itemconfigure(old.item, fill=old.color)
        if old and old.tip:
            tutorial.hide_tip()
        self._hover = hit
        if hit and hit.item:
            self.canvas.itemconfigure(hit.item, fill=hit.hover)
        if hit and hit.tip:
            self._show_tip(hit)
        self.canvas.configure(cursor=("question_arrow" if hit.tip else "hand2")
                              if hit and hit.pointer else "")

    def _on_motion(self, event: tk.Event) -> None:
        self._set_hover(self._hit_at(event.x, event.y))

    def _on_click(self, event: tk.Event) -> None:
        hit = self._hit_at(event.x, event.y)
        if hit:
            hit.on_click()

    def _on_double(self, event: tk.Event) -> None:
        hit = self._hit_at(event.x, event.y)
        if hit and hit.on_double:
            hit.on_double()

    def _on_wheel(self, event: tk.Event) -> None:
        self.turn(-1 if event.delta > 0 else 1)

    # ---- actions ------------------------------------------------------------

    def refresh(self) -> None:
        self.sigils = store.load()
        if self.selected and not store.find(self.sigils, self.selected):
            self.selected = None
        self.draw_pages()

    def select(self, name: str) -> None:
        self.selected = None if self.selected == name else name
        self.draw_pages()

    def turn(self, step: int) -> None:
        self.folio = max(0, self.folio + step)
        self.draw_pages()

    def set_theme(self, name: str) -> None:
        if name == self.theme["name"]:
            return
        self.theme = themes.get(name)
        self.settings["theme"] = name
        store.save_settings(self.settings)
        self.canvas.configure(bg=self.theme["desk"])
        if self.orb:
            self.orb.win.destroy()
            self.orb = CastOrb(self)
        self.redraw()

    def set_status(self, text: str) -> None:
        self.status = text
        item = getattr(self, "status_item", None)
        if item and self.canvas.find_withtag(item):
            self.canvas.itemconfigure(item, text=self._fit(text, "italic", self._status_room()))

    def start_tour(self) -> None:
        """Start (or restart) the guided tour from its first card."""
        if not self.settings.get("tutorial_seen"):
            self.settings["tutorial_seen"] = True
            store.save_settings(self.settings)
        self.tour = tutorial.Tour(self)
        if hasattr(self, "layout"):
            self.draw_pages()

    def new_sigil(self) -> None:
        SigilEditor(self, None)

    def share(self, sigil: store.Sigil) -> None:
        from .share_dialogs import ShareDialog
        ShareDialog(self, sigil)

    def receive(self) -> None:
        from .share_dialogs import ReceiveDialog
        ReceiveDialog(self)

    def edit(self, sigil: store.Sigil) -> None:
        SigilEditor(self, sigil)

    def delete(self, sigil: store.Sigil) -> None:
        if not messagebox.askyesno("Erase sigil", f"Erase “{sigil.name}” from the book?",
                                   parent=self.root):
            return
        store.save([s for s in store.load() if s.name != sigil.name])
        self.selected = None
        self.refresh()
        self.set_status(f"Erased {sigil.name}.")

    def apply_hotkey(self, hotkey: str, initial: bool = False) -> bool:
        try:
            self.app.set_hotkey(hotkey)
        except (ValueError, OSError) as e:
            reason = str(e) if isinstance(e, ValueError) else \
                f"{pretty(hotkey)} is already used by another program."
            if initial:
                self.hotkey_text = f"Hotkey off ({pretty(hotkey)} is taken) · change"
                self.status = "Click the hotkey to pick a different one."
            else:
                messagebox.showerror("Hotkey", reason, parent=self.root)
            return False
        self.hotkey_text = f"Hotkey: {pretty(hotkey)} · change"
        self.settings["hotkey"] = hotkey
        store.save_settings(self.settings)
        if hasattr(self, "layout"):
            self.draw_pages()
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
        on = not self.settings["orb"]
        if on:
            self.show_orb()
        elif self.orb:
            self.orb.win.destroy()
            self.orb = None
        self.settings["orb"] = on
        store.save_settings(self.settings)
        self.draw_pages()

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


# ---- themed widgets for the editor dialog ------------------------------------

def button(parent: tk.Misc, text: str, command, t: dict, primary: bool = False,
           **kw) -> tk.Button:
    bg = t["accent"] if primary else t["field"]
    fg = t["on_accent"] if primary else t["ink"]
    return tk.Button(parent, text=text, command=command, bg=bg, fg=fg, activebackground=fg,
                     activeforeground=bg, relief="flat", bd=0, padx=14, pady=5,
                     font=t["font_button"], cursor="hand2", highlightthickness=1,
                     highlightbackground=t["field_line"], **kw)


def label(parent: tk.Misc, text: str, t: dict, muted: bool = False, font: str = "body",
          **kw) -> tk.Label:
    return tk.Label(parent, text=text, bg=t["page"], fg=t["ink_soft"] if muted else t["ink"],
                    font=t[f"font_{font}"], anchor="w", justify="left", **kw)


class SigilEditor:
    """Dialog to create or edit one sigil: name, what it opens, and its drawings."""

    def __init__(self, book: SigilBook, sigil: store.Sigil | None):
        self.book = book
        self.t = t = book.theme
        self.original = sigil
        self.samples: list[list[Stroke]] = [list(s) for s in sigil.templates] if sigil else []
        self.style = {**DEFAULT_STYLE, **(sigil.style if sigil else {})}

        win = self.win = tk.Toplevel(book.root, bg=t["page"], padx=28, pady=14,
                                     highlightthickness=3, highlightbackground=t["gilt"])
        win.title("Edit sigil" if sigil else "Inscribe a new sigil")
        win.transient(book.root)
        win.resizable(False, False)
        # as big as the screen allows, so there's room to draw
        pad_size = max(380, min(640, win.winfo_screenheight() - 400))

        label(win, "Edit sigil" if sigil else "Inscribe a new sigil", t, font="head") \
            .grid(row=0, column=0, columnspan=2, sticky="w")

        form = tk.Frame(win, bg=t["page"])
        form.grid(row=1, column=0, sticky="nw", padx=(0, 30))
        self._titled(form, "Name", "name").pack(anchor="w")
        self.name_var = tk.StringVar(value=sigil.name if sigil else "")
        self._entry(form, self.name_var).pack(anchor="w", fill="x", pady=(2, 14))

        self._titled(form, "When I draw it, open a…", "kind").pack(anchor="w")
        self.kind_var = tk.StringVar(value=sigil.action["type"] if sigil else "app")
        for kind, text in actions.KINDS.items():
            tk.Radiobutton(form, text=text, value=kind, variable=self.kind_var,
                           command=self._kind_changed, bg=t["page"], fg=t["ink"],
                           selectcolor=t["field"], activebackground=t["page"],
                           activeforeground=t["accent"], font=t["font_body"],
                           cursor="hand2").pack(anchor="w")

        target_title = self._titled(form, "", "target")
        self.target_label = target_title.winfo_children()[0]
        target_title.pack(anchor="w", pady=(14, 0))
        target_row = tk.Frame(form, bg=t["page"])
        target_row.pack(anchor="w", fill="x", pady=2)
        self.target_var = tk.StringVar(value=sigil.action["target"] if sigil else "")
        self._entry(target_row, self.target_var, width=28).pack(side="left")
        self.browse_btn = button(target_row, "Browse…", self.browse, t)
        self.browse_btn.pack(side="left", padx=(6, 0))
        self.target_hint = label(form, "", t, muted=True, font="small", wraplength=300)
        self.target_hint.pack(anchor="w")

        self._titled(form, "Your drawings", "drawings").pack(anchor="w", pady=(22, 0))
        label(form, f"Draw it {RECOMMENDED_SAMPLES} times the same way so it's easy to\n"
              "recognize. Click a drawing to remove it.", t, muted=True,
              font="small").pack(anchor="w")
        self.samples_frame = tk.Frame(form, bg=t["page"])
        self.samples_frame.pack(anchor="w", fill="x", pady=(6, 0))

        pad_col = tk.Frame(win, bg=t["page"])
        pad_col.grid(row=1, column=1, sticky="n")
        self._build_toolbar(pad_col)
        self.pad = DrawPad(pad_col, size=pad_size, bg=t["field"], guide=t["field_line"],
                           on_change=self._update_buttons, ink=t["accent"], style=self.style)
        self.pad.configure(highlightthickness=1, highlightbackground=t["field_line"])
        self.pad.pack(pady=(8, 0))
        pad_buttons = tk.Frame(pad_col, bg=t["page"])
        pad_buttons.pack(fill="x", pady=8)
        button(pad_buttons, "Clear", self.pad.clear, t).pack(side="left")
        tutorial.help_mark(pad_buttons, "clear", t).pack(side="left", padx=(3, 10))
        button(pad_buttons, "↶ Undo", self.pad.undo, t).pack(side="left")
        tutorial.help_mark(pad_buttons, "undo", t).pack(side="left", padx=3)
        tutorial.help_mark(pad_buttons, "add", t).pack(side="right", padx=(3, 0))
        self.add_btn = button(pad_buttons, "Add this drawing", self.add_sample, t, primary=True)
        self.add_btn.pack(side="right")

        bottom = tk.Frame(win, bg=t["page"])
        bottom.grid(row=2, column=0, columnspan=2, sticky="e", pady=(6, 0))
        button(bottom, "Cancel", win.destroy, t).pack(side="left", padx=8)
        button(bottom, "Save sigil", self.save, t, primary=True).pack(side="left")
        tutorial.help_mark(bottom, "save", t).pack(side="left", padx=(3, 0))

        win.bind("<Escape>", lambda e: win.destroy())
        win.bind("<Control-z>", lambda e: self.pad.undo())
        self._kind_changed()
        self._render_samples()
        self._style_changed()
        self._center()
        win.grab_set()
        win.focus_force()

    def _titled(self, parent: tk.Misc, text: str, key: str) -> tk.Frame:
        """A label with a "?" after it."""
        row = tk.Frame(parent, bg=self.t["page"])
        label(row, text, self.t).pack(side="left")
        tutorial.help_mark(row, key, self.t).pack(side="left", padx=(4, 0))
        return row

    def _center(self) -> None:
        win, root = self.win, self.book.root
        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        x = root.winfo_rootx() + (root.winfo_width() - w) // 2
        y = root.winfo_rooty() + (root.winfo_height() - h) // 2
        x = max(0, min(x, win.winfo_screenwidth() - w))
        y = max(0, min(y, win.winfo_screenheight() - h - 48))
        win.geometry(f"+{x}+{y}")

    # ---- pen toolbar ---------------------------------------------------------

    def _build_toolbar(self, parent: tk.Misc) -> None:
        t = self.t
        bar = tk.Frame(parent, bg=t["page"])
        bar.pack(fill="x")

        pens = tk.Frame(bar, bg=t["page"])
        pens.pack(fill="x")
        label(pens, "Pen", t, font="small").pack(side="left")
        tutorial.help_mark(pens, "pen", t).pack(side="left", padx=(2, 8))
        self.pen_buttons: dict[str, tk.Button] = {}
        for pen, name in PENS.items():
            b = button(pens, name, lambda p=pen: self._set_style(pen=p), t)
            b.configure(padx=9, pady=3, font=t["font_small"])
            b.pack(side="left", padx=(0, 4))
            self.pen_buttons[pen] = b

        row = tk.Frame(bar, bg=t["page"])
        row.pack(fill="x", pady=(8, 0))
        label(row, "Size", t, font="small").pack(side="left")
        tutorial.help_mark(row, "size", t).pack(side="left", padx=(2, 4))
        self.size_var = tk.IntVar(value=self.style["size"])
        tk.Scale(row, from_=MIN_SIZE, to=MAX_SIZE, orient="horizontal", length=130,
                 variable=self.size_var, showvalue=False, bg=t["page"], fg=t["ink"],
                 troughcolor=t["field"], highlightthickness=0, bd=0, sliderlength=16,
                 activebackground=t["accent"],
                 command=lambda v: self._set_style(size=int(float(v)))).pack(side="left")
        self.size_label = label(row, "", t, font="small", width=3)
        self.size_label.pack(side="left")
        self.preview = tk.Canvas(row, width=96, height=40, bg=t["field"], highlightthickness=1,
                                 highlightbackground=t["field_line"])
        self.preview.pack(side="left", padx=(6, 14))

        label(row, "Color", t, font="small").pack(side="left")
        tutorial.help_mark(row, "color", t).pack(side="left", padx=(2, 4))
        self.swatches: dict[str | None, tk.Canvas] = {}
        for color in [None, *PALETTE]:
            sw = tk.Canvas(row, width=20, height=20, highlightthickness=2, cursor="hand2",
                           bg=color or t["accent"], highlightbackground=t["page"])
            sw.create_rectangle(0, 0, 19, 19, outline=t["field_line"])
            if color is None:  # the grimoire's own ink
                sw.create_text(10, 10, text="✦", fill=t["page"], font=("Segoe UI Symbol", 8))
            sw.pack(side="left", padx=1)
            sw.bind("<Button-1>", lambda e, c=color: self._set_style(color=c))
            self.swatches[color] = sw
        more = button(row, "More…", self._pick_color, t)
        more.configure(padx=7, pady=1, font=t["font_small"])
        more.pack(side="left", padx=(6, 0))

    def _pick_color(self) -> None:
        _, color = colorchooser.askcolor(color=self.pad.color, parent=self.win,
                                         title="Pick an ink color")
        if color:
            self._set_style(color=color)

    def _set_style(self, **changes) -> None:
        self.style.update(changes)
        self._style_changed()

    def _style_changed(self) -> None:
        t, style = self.t, self.style
        self.pad.set_style(style)
        for pen, b in self.pen_buttons.items():
            on = pen == style["pen"]
            b.configure(bg=t["accent"] if on else t["field"], fg=t["on_accent"] if on else t["ink"])
        for color, sw in self.swatches.items():
            on = color == style["color"]
            sw.configure(highlightbackground=t["ink"] if on else t["page"])
        if self.size_var.get() != style["size"]:
            self.size_var.set(style["size"])
        self.size_label.configure(text=str(style["size"]))
        self.preview.delete("all")
        wave = [(10 + i * 4, 20 + math.sin(i / 2.6) * 9) for i in range(20)]
        render_stroke(self.preview, wave, style["pen"], style["size"], self.pad.color, t["field"])
        self._render_samples()

    def _entry(self, parent: tk.Misc, var: tk.StringVar, width: int = 36) -> tk.Entry:
        t = self.t
        return tk.Entry(parent, textvariable=var, width=width, bg=t["field"], fg=t["ink"],
                        insertbackground=t["accent"], relief="flat", font=t["font_body"],
                        highlightthickness=1, highlightbackground=t["field_line"],
                        highlightcolor=t["accent"])

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
        t = self.t
        for child in self.samples_frame.winfo_children():
            child.destroy()
        n = len(self.samples)
        text = (f"{n} of {RECOMMENDED_SAMPLES} drawings" if n < RECOMMENDED_SAMPLES
                else f"{n} drawings ✓")
        label(self.samples_frame, text, t, muted=True, font="small").pack(anchor="w")
        grid = tk.Frame(self.samples_frame, bg=t["page"])
        grid.pack(anchor="w", pady=4)
        for i, sample in enumerate(self.samples):
            thumb = tk.Canvas(grid, width=88, height=88, bg=t["field"], highlightthickness=1,
                              highlightbackground=t["field_line"], cursor="hand2")
            thumb.grid(row=i // 3, column=i % 3, padx=(0, 8), pady=(0, 8))
            draw_strokes(thumb, sample, 8, 8, 72, 72, t["accent"], 2, style=self.style,
                         bg=t["field"])
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

        sigil = store.Sigil(name, {"type": kind, "target": target}, self.samples,
                            style=dict(self.style))
        if self.original is None:
            others.append(sigil)
        else:
            i = next(i for i, s in enumerate(sigils) if s.name == self.original.name)
            others.insert(i, sigil)
        store.save(others)
        self.book.selected = name
        self.book.refresh()
        self.book.set_status(f"Inscribed {name}.")
        win.destroy()


class CastOrb:
    """Small always-on-top button. Click to cast, drag to move, right-click for a menu."""

    SIZE = 60
    KEY = "#ff00fe"  # transparent color, gives the window a round shape

    def __init__(self, book: SigilBook):
        self.book = book
        t = book.theme
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
        canvas.create_oval(3, 3, size - 3, size - 3, fill=t["page"], outline=t["accent"], width=3)
        canvas.create_oval(9, 9, size - 9, size - 9, outline=t["accent"], width=1)
        canvas.create_text(size / 2, size / 2, text="✦", fill=t["accent"], font=("Segoe UI", 20))

        self.menu = tk.Menu(win, tearoff=False)
        self.menu.add_command(label="Cast a sigil", command=lambda: book.app.summon())
        self.menu.add_command(label="Open Sigil Book", command=book.show)
        self.menu.add_separator()
        self.menu.add_command(label="Hide this button", command=book.toggle_orb)

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


def main() -> None:
    SigilBook().mainloop()
