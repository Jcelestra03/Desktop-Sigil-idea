"""Command line: python -m sigil {run,add,list,remove,test}"""

from __future__ import annotations

import argparse
import os
import sys

from . import actions, app, store
from .hotkey import DEFAULT_HOTKEY
from .recognizer import DEFAULT_MIN_SCORE, compare, recognize


def cmd_run(args: argparse.Namespace) -> int:
    try:
        app.run(args.hotkey)
    except ValueError as e:
        print(e)
        return 1
    except OSError as e:
        print(f"Couldn't register {args.hotkey} ({e.strerror}). Another program is using it;\n"
              f"try another, e.g. python -m sigil run --hotkey ctrl+alt+q")
        return 1
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    sigils = store.load()
    existing = store.find(sigils, args.name)

    action = None
    for kind in ("app", "url", "file"):
        target = getattr(args, kind)
        if target:
            action = {"type": kind, "target": target}
    if existing is None and action is None:
        print("New sigils need an action: --app, --url, or --file.")
        return 1

    n = args.samples
    prompts = [f"Draw the sigil for “{args.name}”  ({i}/{n})" for i in range(1, n + 1)]
    drawings = app.draw_many(prompts, hint="Draw it the same way each time  ·  Esc to cancel")
    if drawings is None:
        print("Cancelled, nothing saved.")
        return 1

    if existing is None:
        sigils.append(store.Sigil(args.name, action, drawings))
        verb = "Added"
    else:
        if action:
            existing.action = action
        existing.templates.extend(drawings)
        verb = "Updated"
    store.save(sigils)
    sigil = store.find(sigils, args.name)
    print(f"{verb} {sigil.name} ({len(sigil.templates)} samples) -> {actions.describe(sigil.action)}")

    _warn_if_confusable(sigil, sigils)
    return 0


def _warn_if_confusable(sigil: store.Sigil, sigils: list[store.Sigil]) -> None:
    others = [s for s in sigils if s is not sigil]
    for template in sigil.templates[-1:]:
        match = recognize(template, others, min_score=0)
        if match and match.score >= DEFAULT_MIN_SCORE + 0.1:
            print(f"  Heads up: this looks a lot like “{match.sigil.name}” "
                  f"(score {match.score:.2f}). Consider a more distinct shape.")
    if len(sigil.templates) > 1:
        a, b = sigil.templates[-2], sigil.templates[-1]
        if compare(a, b) < DEFAULT_MIN_SCORE:
            print("  Heads up: your samples differ a lot from each other. "
                  "Run add again with the same name to add more samples.")


def cmd_list(args: argparse.Namespace) -> int:
    sigils = store.load()
    if not sigils:
        print(f"No sigils yet ({store.sigil_path()}).")
    for s in sigils:
        print(f"{s.name:20} {len(s.templates)} samples  {actions.describe(s.action)}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    sigils = store.load()
    sigil = store.find(sigils, args.name)
    if sigil is None:
        print(f"No sigil named “{args.name}”.")
        return 1
    sigils.remove(sigil)
    store.save(sigils)
    print(f"Removed {sigil.name}.")
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    sigils = store.load()
    strokes = app.draw_once("Test a sigil (nothing will open)")
    if strokes is None:
        print("Cancelled.")
        return 1
    scored = sorted(
        ((max(compare(strokes, t) for t in s.templates), s.name) for s in sigils if s.templates),
        reverse=True,
    )
    for score, name in scored:
        mark = "✔" if score >= DEFAULT_MIN_SCORE else " "
        print(f"{mark} {score:.2f}  {name}")
    if not scored or scored[0][0] < DEFAULT_MIN_SCORE:
        print(f"No match (needs {DEFAULT_MIN_SCORE:.2f}).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sigil", description="Desktop Sigil")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="listen for the hotkey and cast sigils")
    run.add_argument("--hotkey", default=os.environ.get("SIGIL_HOTKEY", DEFAULT_HOTKEY),
                     help=f"e.g. ctrl+alt+s, win+alt+f2 (default {DEFAULT_HOTKEY}, "
                          "or set SIGIL_HOTKEY)")
    run.set_defaults(func=cmd_run)

    add = sub.add_parser("add", help="teach a new sigil (or add samples to an existing one)")
    add.add_argument("name")
    target = add.add_mutually_exclusive_group()
    target.add_argument("--app", help="program to run, e.g. notepad.exe or a full path")
    target.add_argument("--url", help="website to open")
    target.add_argument("--file", help="file or folder to open")
    add.add_argument("--samples", type=int, default=3, help="how many times to draw it (default 3)")
    add.set_defaults(func=cmd_add)

    sub.add_parser("list", help="show your sigils").set_defaults(func=cmd_list)

    remove = sub.add_parser("remove", help="forget a sigil")
    remove.add_argument("name")
    remove.set_defaults(func=cmd_remove)

    sub.add_parser("test", help="draw once and see the scores, without opening anything") \
        .set_defaults(func=cmd_test)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
