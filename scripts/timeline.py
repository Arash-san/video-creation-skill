"""Place the narration on a timeline and write subtitles.

    python timeline.py PROJECT_DIR

Reads narration.json and audio/ (from tts.py). Writes:
  timeline.json  scene starts/durations and each line's start/duration inside its scene
  tl.js          the same data as `const TL = ...` for the page
  narration.wav  the full voice track
  subs.ass       sentence-aware single-line subtitles (burned in by assemble.py)

narration.json knobs (all optional):
  "timing":    {"lead_first": 1.6, "lead": 1.9, "line_gap": 0.45, "tail": 0.7}
  "subtitles": {"font": "Work Sans", "size": 42, "text": "#F4EEE4", "box": "#1E1A16",
                "box_alpha": 0.8, "max_chars": 54, "margin_v": 34, "bold": false}
  per scene:   "min_dur": seconds (stretch a scene that needs more time for its visuals)
  per line:    {"text": "...", "pause": 0.6}  extra silence after that line
"""
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
TAG = re.compile(r"\s*\[[A-Za-z][A-Za-z-]*\]")  # Ming's inline sound tags ([Laughter], [Sigh]) are not subtitled


def ass_color(hexc, alpha=1.0):
    h = hexc.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    a = int(round((1 - alpha) * 255))
    return f"&H{a:02X}{b}{g}{r}".upper()


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def tokens(text, words):
    """Re-attach TTS word timings to the original text so punctuation survives."""
    nchars, nmap = [], []
    for i, ch in enumerate(text):
        if re.match(r"[A-Za-z0-9]", ch):
            nchars.append(ch.lower())
            nmap.append(i)
    ntext = "".join(nchars)
    starts, ptr = [], 0
    for _, _, wt in words:
        nw = norm(wt)
        j = ntext.find(nw, ptr) if nw else -1
        if j < 0:
            starts.append(None)
            continue
        starts.append(nmap[j])
        ptr = j + len(nw)
    idx = [i for i, s in enumerate(starts) if s is not None]
    out = []
    for n, i in enumerate(idx):
        a = starts[i]
        b = starts[idx[n + 1]] if n + 1 < len(idx) else len(text)
        out.append((words[i][0], words[i][1], text[a:b].strip()))
    return out


def _join(t):
    return " ".join(x[2] for x in t)


def _split(sent, maxc):
    text = _join(sent)
    if len(text) <= maxc:
        return [sent]
    n = -(-len(text) // maxc)
    target = len(text) / n
    pieces, cur = [], []
    for i, t in enumerate(sent):
        cur.append(t)
        ln, rest = len(_join(cur)), sent[i + 1:]
        if not rest or len(pieces) == n - 1:
            continue
        comma = t[2].endswith((",", ";", ":"))
        if ((comma and ln >= target * 0.6) or ln >= target) and len(_join(rest)) >= 12:
            pieces.append(cur)
            cur = []
    pieces.append(cur)
    return pieces


def cues(text, words, maxc):
    sentences, cur = [], []
    for t in tokens(text, words):
        cur.append(t)
        if t[2].endswith((".", "?", "!")):
            sentences.append(cur)
            cur = []
    if cur:
        sentences.append(cur)
    groups = []
    for s in sentences:
        for piece in _split(s, maxc):
            if groups and len(_join(piece)) < 22 and len(_join(groups[-1] + piece)) <= maxc:
                groups[-1] = groups[-1] + piece
            else:
                groups.append(piece)
    return [[g[0][0], g[-1][1], _join(g)] for g in groups if g]


def pcm(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32)


def ts(t):
    h, rem = divmod(max(0.0, t), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def main(project):
    cfg = json.loads((project / "narration.json").read_text(encoding="utf-8"))
    A = project / "audio"
    durs = json.loads((A / "durations.json").read_text())
    fj = A / "files.json"
    files = json.loads(fj.read_text()) if fj.exists() else {k: f"{k}.mp3" for k in durs}
    tm = {"lead_first": 1.6, "lead": 1.9, "line_gap": 0.45, "tail": 0.7, **cfg.get("timing", {})}
    st = {"font": "Work Sans", "size": 42, "text": "#F4EEE4", "box": "#1E1A16", "box_alpha": 0.8,
          "max_chars": 54, "margin_v": 34, "bold": False, **cfg.get("subtitles", {})}
    fps = cfg.get("fps", 30)

    t, scenes, placed = 0.0, [], []
    for si, sc in enumerate(cfg["scenes"]):
        start, lt, lines = t, tm["lead_first"] if si == 0 else tm["lead"], []
        for n, ln in enumerate(sc["lines"]):
            key = f"{sc['id']}_{n}"
            text = ln if isinstance(ln, str) else ln["text"]
            pause = 0.0 if isinstance(ln, str) else ln.get("pause", 0.0)
            lines.append({"t": round(lt, 3), "d": round(durs[key], 3)})
            placed.append((start + lt, key, text))
            lt += durs[key] + tm["line_gap"] + pause
        dur = max(lt - tm["line_gap"] + tm["tail"], sc.get("min_dur", 0))
        scenes.append({"id": sc["id"], "start": round(start, 3), "dur": round(dur, 3), "lines": lines})
        t += dur
    total = t
    tl = {"total": round(total, 3), "fps": fps, "width": cfg.get("width", 1920), "height": cfg.get("height", 1080),
          "subtitle_top": cfg.get("subtitle_top", 900), "scenes": scenes}
    (project / "timeline.json").write_text(json.dumps(tl, indent=1))
    (project / "tl.js").write_text("const TL = " + json.dumps(tl) + ";\n")

    buf = np.zeros(int((total + 1) * SR), dtype=np.float32)
    for t0, key, _ in placed:
        x = pcm(A / files[key])
        i = int(t0 * SR)
        buf[i:i + len(x)] += x
    buf = np.clip(buf, -32767, 32767).astype(np.int16)
    with wave.open(str(project / "narration.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(buf.tobytes())

    events = []
    for t0, key, text in placed:
        words = json.loads((A / f"{key}.words.json").read_text())
        for a, b, txt in cues(TAG.sub("", text), words, st["max_chars"]):
            events.append([t0 + a, t0 + b, txt])
    for i, e in enumerate(events):  # hold each cue a little, never into the next one
        nxt = events[i + 1][0] if i + 1 < len(events) else e[1] + 1
        e[1] = min(nxt - 0.02, e[1] + 0.8) if nxt - e[1] < 1.2 else e[1] + 0.5
    W, H = tl["width"], tl["height"]
    tc, bc = ass_color(st["text"]), ass_color(st["box"], st["box_alpha"])
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{st['font']},{st['size']},{tc},{tc},{bc},{bc},{-1 if st['bold'] else 0},0,0,0,100,100,0.3,0,3,13,0,2,150,150,{st['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    body = "\n".join(f"Dialogue: 0,{ts(a)},{ts(b)},Sub,,0,0,0,,{x}" for a, b, x in events)
    (project / "subs.ass").write_text(head + body + "\n", encoding="utf-8")
    print(f"total {total:.1f}s ({total / 60:.1f} min), {len(events)} cues, longest cue {max(len(e[2]) for e in events)} chars")
    for s in scenes:
        print(f"  {s['id']:14s} start {s['start']:7.2f}  dur {s['dur']:6.2f}  lines {len(s['lines'])}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]).resolve())
