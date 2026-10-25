"""Synthesize every narration line and keep word timings for subtitles and cues.

    python tts.py PROJECT_DIR

Reads PROJECT_DIR/narration.json. Writes PROJECT_DIR/audio/<scene>_<n>.wav (Ming) or .mp3 (edge-tts),
plus <key>.words.json, durations.json and files.json. A line is re-synthesized only when its text or
the voice settings change, so you can edit one sentence and rerun cheaply.

Engines (narration.json "tts" block, see references/narration.md):
  ming  Ming-3.0-tts-0.5B, a local open-weight model (needs an NVIDIA GPU with about 4 GB free).
        Built-in voices, a voice designed from a description, or a cloned voice. Install once with
        `python scripts/setup_ming.py`. Word timings come from forced alignment.
  edge  Microsoft Edge neural voices through edge-tts (free, needs internet, no GPU).
  auto  (default) ming when it is installed and a GPU is visible, otherwise edge.
"""
import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MING_VOICES = ("US_James", "US_Emma", "US_Stella", "UK_George", "UK_Charlotte")
DEFAULT_ANCHOR = ("Every map leaves something out. The trick is choosing what to keep, "
                  "and then telling the story clearly, one step at a time.")


def ming_home():
    return Path(os.environ.get("MING_TTS_HOME", Path.home() / ".cache" / "video-creation" / "ming"))


def ming_python(home):
    for p in (home / "venv" / "Scripts" / "python.exe", home / "venv" / "bin" / "python"):
        if p.exists():
            return p
    return None


def ming_ready():
    home = ming_home()
    return bool(ming_python(home) and (home / "model" / "model.safetensors").exists() and shutil.which("nvidia-smi"))


def load(project):
    cfg = json.loads((project / "narration.json").read_text(encoding="utf-8"))
    lines = []
    for sc in cfg["scenes"]:
        for n, ln in enumerate(sc["lines"]):
            text = ln if isinstance(ln, str) else ln["text"]
            lines.append((f"{sc['id']}_{n}", text))
    return cfg, lines


def settings(cfg):
    """Merge the "tts" block with the older top-level "voice"/"rate" keys."""
    t = dict(cfg.get("tts", {}))
    legacy = "tts" not in cfg and "voice" in cfg  # older projects named an edge-tts voice directly
    engine = t.get("engine", "edge" if legacy else "auto")
    if engine == "auto":
        engine = "ming" if ming_ready() else "edge"
        if engine == "edge":
            print("tts: Ming is not installed or no GPU is visible, using edge-tts "
                  "(install Ming with: python scripts/setup_ming.py)", file=sys.stderr)
    if engine == "edge":
        voice = t.get("edge_voice") or cfg.get("voice") or "en-US-AvaMultilingualNeural"
        if voice in MING_VOICES:
            voice = "en-US-AvaMultilingualNeural"
        return {"engine": "edge", "voice": voice, "rate": t.get("edge_rate") or cfg.get("rate", "+4%")}
    if "design" in t:
        voice = {"mode": "design", "design": t["design"], "anchor_text": t.get("anchor_text", DEFAULT_ANCHOR)}
    elif "clone" in t:
        voice = {"mode": "clone", "clone": t["clone"], "clone_text": t["clone_text"]}
    else:
        name = t.get("voice", "US_James")
        if name not in MING_VOICES:
            raise SystemExit(f"tts: unknown Ming voice {name!r}; choose one of {', '.join(MING_VOICES)}, "
                             "or use \"design\" / \"clone\"")
        voice = {"mode": "builtin", "name": name, "lock": bool(t.get("lock", True)),
                 "anchor_text": t.get("anchor_text", DEFAULT_ANCHOR)}
    for k in ("language", "cfg", "sigma", "temperature"):
        if k in t:
            voice[k] = t[k]
    return {"engine": "ming", "voice": voice, "tempo": float(t.get("tempo", 1.0)), "workers": int(t.get("workers", 3)),
            "retries": int(t.get("retries", 2))}


def sig_of(st, text):
    keep = {k: v for k, v in st.items() if k not in ("workers", "retries")}  # these do not change the audio
    return hashlib.sha1(json.dumps([keep, text], sort_keys=True).encode()).hexdigest()


def fresh(out, key, ext, sig):
    meta = out / f"{key}.meta"
    return (out / f"{key}.{ext}").exists() and (out / f"{key}.words.json").exists() \
        and meta.exists() and meta.read_text() == sig


# ---------------------------------------------------------------- edge-tts

async def edge_synth(out, key, text, st, sig, sem):
    import edge_tts
    mp3, wj, meta = out / f"{key}.mp3", out / f"{key}.words.json", out / f"{key}.meta"
    async with sem:
        for attempt in range(5):
            try:
                spoken = re.sub(r"\s*\[[A-Za-z][A-Za-z-]*\]", "", text)  # Ming-only sound tags
                com = edge_tts.Communicate(spoken, st["voice"], rate=st["rate"], boundary="WordBoundary")
                audio, words = bytearray(), []
                async for ch in com.stream():
                    if ch["type"] == "audio":
                        audio.extend(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        words.append([ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]])
                if not audio:
                    raise RuntimeError("empty audio")
                mp3.write_bytes(bytes(audio))
                wj.write_text(json.dumps(words))
                meta.write_text(sig)
                return
            except Exception as e:  # the service drops connections now and then
                print(key, "retry", attempt, e, file=sys.stderr)
                await asyncio.sleep(2 + attempt * 2)
        raise RuntimeError(f"tts failed: {key}")


def run_edge(out, todo, st):
    async def go():
        sem = asyncio.Semaphore(4)
        await asyncio.gather(*(edge_synth(out, k, t, st, s, sem) for k, t, s in todo))
    asyncio.run(go())


# ---------------------------------------------------------------- Ming

def gpu_slots(n_want, per_worker_mb=4500):
    """GPU index for each worker: the emptiest GPUs first, several workers per GPU when memory allows."""
    if os.environ.get("CUDA_VISIBLE_DEVICES"):
        return [os.environ["CUDA_VISIBLE_DEVICES"]] * n_want
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.free", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, check=True)
        free = sorted((tuple(int(x) for x in ln.split(",")) for ln in r.stdout.strip().splitlines()),
                      key=lambda f: -f[1])
    except Exception:
        return [None]
    slots, k = [], 0
    while len(slots) < n_want and k < 8:  # round-robin over GPUs with room
        added = False
        for idx, mb in free:
            if mb - k * per_worker_mb >= per_worker_mb and len(slots) < n_want:
                slots.append(str(idx))
                added = True
        if not added:
            break
        k += 1
    if not slots:
        idx, mb = free[0]
        print(f"tts: warning, the emptiest GPU has only {mb} MB free", file=sys.stderr)
        slots = [str(idx)]
    return slots


def start_worker(py, job, jp, gpu):
    job = {**job, "report": str(jp.with_suffix(".report.json"))}
    jp.write_text(json.dumps(job, indent=1, ensure_ascii=False), encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "TQDM_DISABLE": "1",
           "TRANSFORMERS_VERBOSITY": "error", "PYTHONWARNINGS": "ignore"}
    if gpu is not None:
        env.update(CUDA_DEVICE_ORDER="PCI_BUS_ID", CUDA_VISIBLE_DEVICES=gpu)
    log = open(jp.with_suffix(".log"), "w", encoding="utf-8")
    return subprocess.Popen([str(py), str(HERE / "ming_worker.py"), str(jp)], env=env,
                            stdout=log, stderr=subprocess.STDOUT), log


def wait_workers(procs):
    import time
    seen = {}
    while True:
        alive = False
        for p, log, jp in procs:
            alive |= p.poll() is None
            lines = jp.with_suffix(".log").read_text(encoding="utf-8", errors="replace").splitlines()
            for ln in lines[seen.get(jp, 0):]:
                if ln.startswith("ming:"):
                    print(ln, flush=True)
            seen[jp] = len(lines)
        if not alive:
            break
        time.sleep(1)
    for p, log, jp in procs:
        log.close()
        if p.returncode != 0:
            tail = jp.with_suffix(".log").read_text(encoding="utf-8", errors="replace").splitlines()[-30:]
            print("\n".join(tail), file=sys.stderr)
            raise SystemExit(f"tts: Ming worker failed, full log in {jp.with_suffix('.log')}")


def run_ming(project, out, todo, st):
    home = ming_home()
    py = ming_python(home)
    if not py:
        raise SystemExit(f"tts: Ming is not installed in {home}. Run: python scripts/setup_ming.py")
    voice = dict(st["voice"])
    if voice["mode"] == "clone":
        voice["clone"] = str((project / voice["clone"]).resolve())
    base = {"repo": str(home / "repo"), "model": str(home / "model"), "device": "cuda:0",
            "voice": voice, "tempo": st["tempo"], "retries": st["retries"], "anchor_dir": str(out)}
    item = lambda k, t, s: {"key": k, "text": t, "sig": s, "wav": str(out / f"{k}.wav"),
                            "words": str(out / f"{k}.words.json"), "meta": str(out / f"{k}.meta")}
    # Each worker holds its own copy of the model (about 3 GB). Generation is many small GPU steps,
    # so a few workers side by side run several times faster than one.
    n = max(1, min(st["workers"], len(todo)))
    slots = gpu_slots(n)
    if voice["mode"] == "design" or voice.get("lock"):  # make the shared voice anchor before the workers start
        jp = out / "ming_job_anchor.json"
        wait_workers([(*start_worker(py, {**base, "lines": []}, jp, slots[0]), jp)])
    order = sorted(todo, key=lambda x: -len(x[1]))  # longest first, dealt round-robin
    procs = []
    for w, gpu in enumerate(slots):
        part = order[w::len(slots)]
        if part:
            jp = out / f"ming_job_{w}.json"
            procs.append((*start_worker(py, {**base, "lines": [item(*x) for x in part]}, jp, gpu), jp))
    print(f"tts: {len(procs)} Ming worker(s) on GPU {', '.join(sorted(set(str(g) for g in slots)))}")
    wait_workers(procs)
    # Merge the listening-check results into audio/voice_report.json (cached lines keep their old entry).
    rp = out / "voice_report.json"
    report = {r["key"]: r for r in json.loads(rp.read_text())} if rp.exists() else {}
    for _, _, jp in procs:
        for r in json.loads(jp.with_suffix(".report.json").read_text()):
            report[r["key"]] = r
    rp.write_text(json.dumps(list(report.values()), indent=1))
    bad = [r for r in report.values() if not r["ok"]]
    if bad:
        print(f"tts: {len(bad)} line(s) still failed the listening check after retries "
              f"(see {rp}); rephrase them and rerun:")
        for r in bad:
            print(f"   {r['key']}: unclear words {r['unclear_words']}, voice similarity {r['voice_similarity']}")
    else:
        print("tts: listening check passed for every line (script match and same voice)")


# ---------------------------------------------------------------- main

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main(project):
    cfg, lines = load(project)
    out = project / "audio"
    out.mkdir(exist_ok=True)
    st = settings(cfg)
    ext = "wav" if st["engine"] == "ming" else "mp3"
    todo = []
    for k, t in lines:
        s = sig_of(st, t)
        if not fresh(out, k, ext, s):
            todo.append((k, t, s))
    label = st["voice"] if st["engine"] == "edge" else st["voice"].get("name") or st["voice"]["mode"]
    print(f"tts: engine {st['engine']}, voice {label}, {len(todo)} of {len(lines)} lines to synthesize")
    if todo:
        (run_ming(project, out, todo, st) if st["engine"] == "ming" else run_edge(out, todo, st))
    files = {k: f"{k}.{ext}" for k, _ in lines}
    durs = {k: duration(out / f) for k, f in files.items()}
    (out / "files.json").write_text(json.dumps(files, indent=1))
    (out / "durations.json").write_text(json.dumps(durs, indent=1))
    print(f"{len(lines)} lines ({len(todo)} new), {sum(durs.values()) / 60:.1f} min of speech")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]).resolve())
