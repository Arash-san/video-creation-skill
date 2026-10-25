"""Propose fresh art directions for a new video, avoiding styles used before.

    python style_roll.py [--n 4] [--seed 7] [--log PATH]          print N candidate directions
    python style_roll.py --record "Risograph zine" --title "Hash tables" [--log PATH]
    python style_roll.py --history [--log PATH]

Each candidate combines a medium, a transition, a camera, a through-line, an energy, a layout and a
narrator voice from references/style_axes.json. One candidate is always a hybrid of two media, which is often
where the most original looks come from. Media already in the log are skipped.
The log defaults to ~/.video-creation/styles.jsonl (override with --log or VIDEO_STYLE_LOG).
"""
import argparse
import json
import os
import random
import time
from pathlib import Path

AXES = Path(__file__).resolve().parent.parent / "references" / "style_axes.json"


def log_path(arg):
    p = Path(arg or os.environ.get("VIDEO_STYLE_LOG") or Path.home() / ".video-creation" / "styles.jsonl")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def history(p):
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--log", default=None)
    ap.add_argument("--record", default=None, help="name of the direction you chose")
    ap.add_argument("--title", default="", help="video title, stored with --record")
    ap.add_argument("--notes", default="", help="palette/type/motif summary, stored with --record")
    ap.add_argument("--history", action="store_true")
    a = ap.parse_args()
    lp = log_path(a.log)

    if a.record:
        with lp.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"date": time.strftime("%Y-%m-%d"), "style": a.record, "title": a.title, "notes": a.notes}) + "\n")
        print(f"recorded '{a.record}' in {lp}")
        return
    past = history(lp)
    if a.history:
        for h in past:
            print(f"{h['date']}  {h['style']:32s} {h.get('title', '')}  {h.get('notes', '')}")
        print(f"{len(past)} entries in {lp}")
        return

    ax = json.loads(AXES.read_text(encoding="utf-8"))
    used = " | ".join(h["style"].lower() for h in past)
    media = [m for m in ax["media"] if m["name"].lower() not in used] or ax["media"]
    rnd = random.Random(a.seed if a.seed is not None else time.time_ns())
    picks = rnd.sample(media, min(len(media), a.n + 1))
    print(f"{len(past)} past styles skipped. Candidates (adapt one to the topic, or invent beyond them):\n")
    for i in range(min(a.n, len(picks))):
        m = picks[i]
        hybrid = i == a.n - 1 and len(picks) > a.n
        name = f"{m['name']} x {picks[-1]['name']}" if hybrid else m["name"]
        print(f"{i + 1}. {name}{'   (hybrid)' if hybrid else ''}")
        print(f"   world:      {m['world']}")
        if hybrid:
            print(f"   blend with: {picks[-1]['world']}")
        print(f"   palette:    {' '.join(m['palette'])}")
        print(f"   texture:    {m['texture']}")
        print(f"   type:       display {m['type'][0]} / text {m['type'][1]} / numbers {m['type'][2]}")
        print(f"   moves:      {'; '.join(m['moves'])}")
        print(f"   transition: {rnd.choice(ax['transitions'])}")
        print(f"   camera:     {rnd.choice(ax['camera'])}")
        print(f"   through:    {rnd.choice(ax['through_lines'])}")
        print(f"   energy:     {rnd.choice(ax['energy'])}")
        print(f"   layout:     {rnd.choice(ax['layout'])}")
        print(f"   voice:      {rnd.choice(ax['voices'])}\n")
    print("After choosing, record it:  python style_roll.py --record \"<name>\" --title \"<video>\" --notes \"<palette, type, motif>\"")


if __name__ == "__main__":
    main()
