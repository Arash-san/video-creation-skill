"""Join rendered chunks, add the narration, burn in subtitles, and optionally split for size-capped uploads.

    python assemble.py PROJECT_DIR --name my_video [--split-mb 50] [--parts K | --cut-at sceneA,sceneB]

Writes PROJECT_DIR/deliverables/<name>_1080p.mp4 (CRF 20). With --split-mb, also writes parts
cut at scene boundaries, each encoded to fit under the cap (for chat apps with upload limits).
"""
import argparse
import json
import math
import subprocess
from pathlib import Path


def run(args, cwd):
    subprocess.run(args, check=True, cwd=cwd)


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--name", default="video")
    ap.add_argument("--split-mb", type=float, default=0)
    ap.add_argument("--parts", type=int, default=0)
    ap.add_argument("--cut-at", default="")
    ap.add_argument("--crf", type=int, default=20)
    a = ap.parse_args()
    P = Path(a.project).resolve()
    out = P / "deliverables"
    out.mkdir(exist_ok=True)
    full = out / f"{a.name}_1080p.mp4"
    # libass needs static fonts; fetch_fonts.py puts static copies of variable fonts in fonts/subs
    fonts = "fonts/subs" if (P / "fonts" / "subs").exists() else "fonts" if (P / "fonts").exists() else "."

    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "chunks/list.txt", "-c", "copy", "joined.mp4"], P)
    run(["ffmpeg", "-v", "error", "-y", "-i", "joined.mp4", "-i", "narration.wav", "-vf", f"ass=subs.ass:fontsdir={fonts}",
         "-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(full)], P)
    total = dur(full)
    print(f"{full.name}: {total:.1f}s, {full.stat().st_size / 1e6:.1f} MB")
    if not a.split_mb:
        return

    tl = json.loads((P / "timeline.json").read_text())
    starts = [s["start"] for s in tl["scenes"]]
    if a.cut_at:
        ids = a.cut_at.split(",")
        cuts = [next(s["start"] for s in tl["scenes"] if s["id"] == i) for i in ids]
    else:
        # enough parts that each keeps >= ~700 kbps video
        k = a.parts or max(1, math.ceil(total * 0.8e6 / 8 / (a.split_mb * 0.92e6)))
        cuts = []
        for i in range(1, k):
            target = total * i / k
            cuts.append(min(starts[1:], key=lambda s: abs(s - target)))
        cuts = sorted(set(cuts))
    bounds = [0.0] + cuts + [total]
    for i in range(len(bounds) - 1):
        s, e = bounds[i], bounds[i + 1]
        part = out / f"{a.name}_part{i + 1}.mp4"
        kbps = int(a.split_mb * 0.92e6 * 8 / (e - s) / 1000) - 96
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(full), "-vf", "hqdn3d=1.5:1.5:4:4",
             "-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.6)}k",
             "-bufsize", f"{kbps * 3}k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(part)], P)
        mb = part.stat().st_size / 1e6
        print(f"{part.name}: {dur(part):.1f}s, {mb:.1f} MB{'  OVER CAP' if mb > a.split_mb else ''}")


if __name__ == "__main__":
    main()
