"""Render frames of PROJECT_DIR/index.html in headless Chromium.

    python render.py PROJECT_DIR stills T1 T2 ...      PNG stills at those seconds + contact.png
    python render.py PROJECT_DIR sheet N [K]           K stills spread over scene N -> stills/sheetN.png
    python render.py PROJECT_DIR sheets [K]            one contact sheet per scene
    python render.py PROJECT_DIR check [STEP]          layout check every STEP s (default 0.5)
    python render.py PROJECT_DIR video [WORKERS]       render every frame in parallel chunks -> chunks/

The page must define window.renderFrame(t), window.grab() and set window.READY (the template does).
Needs: pip install playwright && python -m playwright install chromium; ffmpeg on PATH.
"""
import base64
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

PROJECT = None
TL = None


def setup(project):
    global PROJECT, TL
    PROJECT = Path(project).resolve()
    TL = json.loads((PROJECT / "timeline.json").read_text())
    (PROJECT / "tl.js").write_text("const TL = " + json.dumps(TL) + ";\n")


def page_ctx(project):
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    br = pw.chromium.launch(args=["--disable-gpu", "--force-color-profile=srgb",
                                  "--allow-file-access-from-files", "--disable-web-security"])
    pg = br.new_page(viewport={"width": TL.get("width", 1920), "height": TL.get("height", 1080)})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    pg.goto((Path(project) / "index.html").as_uri())
    try:
        pg.wait_for_function("window.READY === true", timeout=60000)
    except Exception:
        raise SystemExit("page never set window.READY. Errors:\n  " + "\n  ".join(errs or ["(none logged)"]))
    return pw, br, pg, errs


def frame_png(pg, t):
    url = pg.evaluate(f"(renderFrame({t:.4f}), grab())")
    return base64.b64decode(url.split(",", 1)[1])


def stills(ts, out_dir="stills"):
    pw, br, pg, errs = page_ctx(PROJECT)
    d = PROJECT / out_dir
    d.mkdir(parents=True, exist_ok=True)
    paths = []
    for t in ts:
        p = d / f"t{float(t):07.2f}.png"
        p.write_bytes(frame_png(pg, float(t)))
        paths.append(p)
    br.close()
    pw.stop()
    if errs:
        print("PAGE ERRORS:", *errs[:10], sep="\n  ")
    return paths


def contact(paths, out, cols=4):
    n = len(paths)
    if n == 1:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(paths[0]), "-vf", "scale=640:-2", str(out)], check=True)
        return
    args = ["ffmpeg", "-v", "error", "-y"]
    for p in paths:
        args += ["-i", str(p)]
    inputs = "".join(f"[{i}:v]scale=640:360[s{i}];" for i in range(n))
    layout = "|".join(f"{(i % cols) * 640}_{(i // cols) * 360}" for i in range(n))
    args += ["-filter_complex", inputs + "".join(f"[s{i}]" for i in range(n)) + f"xstack=inputs={n}:layout={layout}:fill=black", str(out)]
    subprocess.run(args, check=True)


def sheet(n, k=12):
    s = TL["scenes"][n]
    ts = [s["start"] + (s["dur"] - 0.05) * (i + 1) / k for i in range(k)]
    ps = stills(ts, f"stills/s{n}")
    contact(ps, PROJECT / "stills" / f"sheet{n:02d}_{s['id']}.png")
    return ts


def check(step=0.5):
    """Sample frames and report text that overlaps other text, leaves the frame, or enters the subtitle band."""
    W, H = TL.get("width", 1920), TL.get("height", 1080)
    sub_top, margin = TL.get("subtitle_top", 900), 24
    pw, br, pg, errs = page_ctx(PROJECT)
    pg.evaluate("window.LAYOUT = true")
    issues, seen = [], set()
    t = 0.0
    while t < TL["total"]:
        data = json.loads(pg.evaluate(f"(renderFrame({t:.3f}), JSON.stringify({{b: window.__boxes || [], tr: !!window.__inTransition}}))"))
        if not data["tr"]:
            boxes = [b for b in data["b"] if b["a"] > 0.35]
            scene = next(s["id"] for s in reversed(TL["scenes"]) if t >= s["start"])
            for b in boxes:
                why = []
                if b["x0"] < margin or b["x1"] > W - margin or b["y0"] < margin:
                    why.append("outside frame margin")
                if b["y1"] > sub_top and not b.get("sub"):
                    why.append(f"in subtitle band (bottom {b['y1']:.0f} > {sub_top})")
                for w in why:
                    key = (scene, b["s"], w)
                    if key not in seen:
                        seen.add(key)
                        issues.append(f"{t:7.2f}s  [{scene}] '{b['s'][:40]}' {w}")
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    p, q = boxes[i], boxes[j]
                    ix = min(p["x1"], q["x1"]) - max(p["x0"], q["x0"])
                    iy = min(p["y1"], q["y1"]) - max(p["y0"], q["y0"])
                    if ix <= 2 or iy <= 2:
                        continue
                    small = min((p["x1"] - p["x0"]) * (p["y1"] - p["y0"]), (q["x1"] - q["x0"]) * (q["y1"] - q["y0"]))
                    if ix * iy > 0.12 * small and ix * iy > 120:
                        key = (scene, p["s"], q["s"])
                        if key not in seen:
                            seen.add(key)
                            issues.append(f"{t:7.2f}s  [{scene}] overlap: '{p['s'][:30]}' x '{q['s'][:30]}'")
        t += step
    br.close()
    pw.stop()
    for e in errs[:10]:
        issues.insert(0, "PAGE ERROR: " + e)
    print("\n".join(issues) if issues else "layout check: no text problems found")
    print(f"{len(issues)} issue(s). Text boxes only; shapes and images still need a look at the contact sheets.")
    return issues


def chunk(args):
    project, k, f0, f1, fps = args
    setup(project)
    out = PROJECT / "chunks" / f"c{k:03d}.mp4"
    ok = PROJECT / "chunks" / f"c{k:03d}.ok"
    if out.exists() and ok.exists():
        return k, 0.0
    pw, br, pg, errs = page_ctx(PROJECT)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "png", "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(out)],
                          stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        ff.stdin.write(frame_png(pg, f / fps))
    ff.stdin.close()
    ff.wait()
    br.close()
    pw.stop()
    if errs:
        (PROJECT / "chunks" / f"c{k:03d}.err").write_text("\n".join(errs))
    ok.write_text(f"{f1 - f0} frames {time.time() - t0:.0f}s\n")
    return k, time.time() - t0


def video(workers):
    (PROJECT / "chunks").mkdir(exist_ok=True)
    fps = TL.get("fps", 30)
    nfr = int(TL["total"] * fps) + 1
    size = 300
    jobs = [(str(PROJECT), k, f0, min(nfr, f0 + size), fps) for k, f0 in enumerate(range(0, nfr, size))]
    t0 = time.time()
    with ProcessPoolExecutor(workers) as ex:
        for k, dt in ex.map(chunk, jobs):
            print(f"chunk {k + 1}/{len(jobs)} {dt:.0f}s  elapsed {time.time() - t0:.0f}s", flush=True)
    (PROJECT / "chunks" / "list.txt").write_text("".join(f"file 'c{j[1]:03d}.mp4'\n" for j in jobs))
    errs = list((PROJECT / "chunks").glob("*.err"))
    if errs:
        print("page errors in", [e.name for e in errs])
    print(f"{nfr} frames in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    setup(sys.argv[1])
    mode, rest = sys.argv[2], sys.argv[3:]
    if mode == "stills":
        ps = stills(rest)
        contact(ps, PROJECT / "stills" / "contact.png")
        print("wrote", len(ps), "stills + stills/contact.png")
    elif mode == "sheet":
        print("ok", [round(t, 1) for t in sheet(int(rest[0]), int(rest[1]) if len(rest) > 1 else 12)])
    elif mode == "sheets":
        for n in range(len(TL["scenes"])):
            sheet(n, int(rest[0]) if rest else 8)
        print("wrote", len(TL["scenes"]), "sheets in stills/")
    elif mode == "check":
        check(float(rest[0]) if rest else 0.5)
    elif mode == "video":
        video(int(rest[0]) if rest else max(1, min(8, (os.cpu_count() or 4) // 2)))
    else:
        raise SystemExit(__doc__)
