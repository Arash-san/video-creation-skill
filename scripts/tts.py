"""Synthesize every narration line with edge-tts and keep word timings for subtitles.

    python tts.py PROJECT_DIR

Reads PROJECT_DIR/narration.json. Writes PROJECT_DIR/audio/<scene>_<n>.mp3 plus .words.json.
A line is re-synthesized only when its text, voice or rate changes, so you can edit
one sentence and rerun cheaply.
"""
import asyncio
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import edge_tts


def load(project):
    cfg = json.loads((project / "narration.json").read_text(encoding="utf-8"))
    lines = []
    for sc in cfg["scenes"]:
        for n, ln in enumerate(sc["lines"]):
            text = ln if isinstance(ln, str) else ln["text"]
            lines.append((f"{sc['id']}_{n}", text))
    return cfg, lines


async def synth(out, key, text, voice, rate, sem):
    mp3, wj, meta = out / f"{key}.mp3", out / f"{key}.words.json", out / f"{key}.meta"
    sig = hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()
    if mp3.exists() and wj.exists() and meta.exists() and meta.read_text() == sig:
        return False
    async with sem:
        for attempt in range(5):
            try:
                com = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
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
                return True
            except Exception as e:  # the service drops connections now and then
                print(key, "retry", attempt, e, file=sys.stderr)
                await asyncio.sleep(2 + attempt * 2)
        raise RuntimeError(f"tts failed: {key}")


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


async def main(project):
    cfg, lines = load(project)
    out = project / "audio"
    out.mkdir(exist_ok=True)
    voice, rate = cfg.get("voice", "en-US-AvaMultilingualNeural"), cfg.get("rate", "+4%")
    sem = asyncio.Semaphore(4)
    done = await asyncio.gather(*(synth(out, k, t, voice, rate, sem) for k, t in lines))
    durs = {k: duration(out / f"{k}.mp3") for k, _ in lines}
    (out / "durations.json").write_text(json.dumps(durs, indent=1))
    print(f"{len(lines)} lines ({sum(done)} new), {sum(durs.values()) / 60:.1f} min of speech")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    asyncio.run(main(Path(sys.argv[1]).resolve()))
