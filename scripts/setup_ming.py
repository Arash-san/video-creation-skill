"""Install Ming-3.0-tts (Ant Group / inclusionAI, MIT license) for tts.py. Run once per machine.

    python setup_ming.py [--home DIR] [--cuda cu128|cu124] [--no-test]

Creates DIR (default ~/.cache/video-creation/ming, or $MING_TTS_HOME) with:
  repo/   the inference code from github.com/inclusionAI/Ming-3.0-tts
  model/  the inclusionAI/Ming-3.0-tts-0.5B checkpoint from Hugging Face (about 3 GB)
  venv/   its own Python environment (PyTorch, transformers 4.46), separate from yours
It also fetches the small forced-alignment model used for word timings, then synthesizes one test line.

Needs an NVIDIA GPU with about 4 GB free per worker, git, and Python 3.10 to 3.12 (uv is used when present).
--cuda cu128 (default) installs PyTorch 2.7.1, which runs on RTX 20 to 50 series and needs driver 570 or newer.
--cuda cu124 installs PyTorch 2.6.0 (the version upstream tested) for older drivers; it does not run on RTX 50 series.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "https://github.com/inclusionAI/Ming-3.0-tts.git"
COMMIT = "028c1eace193e7acdb256453da89b6e9207e052b"  # tested 2026-10-24
MODEL = "inclusionAI/Ming-3.0-tts-0.5B"
TORCH = {"cu128": ("2.7.1", "2.7.1"), "cu124": ("2.6.0", "2.6.0")}


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    default = os.environ.get("MING_TTS_HOME", str(Path.home() / ".cache" / "video-creation" / "ming"))
    ap.add_argument("--home", default=default)
    ap.add_argument("--cuda", choices=sorted(TORCH), default="cu128")
    ap.add_argument("--no-test", action="store_true")
    a = ap.parse_args()
    home = Path(a.home).expanduser().resolve()
    home.mkdir(parents=True, exist_ok=True)

    if not shutil.which("nvidia-smi"):
        print("No NVIDIA GPU found (nvidia-smi is missing). Ming needs one; tts.py will keep using edge-tts.")
        sys.exit(1)
    for tool in ("git", "ffmpeg"):
        if not shutil.which(tool):
            sys.exit(f"{tool} is required")

    repo = home / "repo"
    if not (repo / "ming_tts.py").exists():
        run(["git", "clone", "-q", REPO, repo])
    run(["git", "-C", repo, "fetch", "-q", "origin", COMMIT])
    run(["git", "-C", repo, "checkout", "-q", COMMIT])

    venv = home / "venv"
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    uv = shutil.which("uv")
    if not py.exists():
        if uv:
            run([uv, "venv", "-q", "-p", "3.11", venv])
        else:
            if not (3, 10) <= sys.version_info[:2] <= (3, 12):
                sys.exit("Use Python 3.10 to 3.12 to run this script, or install uv")
            run([sys.executable, "-m", "venv", venv])
    pip = [uv, "pip", "install", "-q", "--python", py] if uv else [py, "-m", "pip", "install", "-q"]
    tv, av = TORCH[a.cuda]
    run(pip + [f"torch=={tv}", f"torchaudio=={av}", "--index-url", f"https://download.pytorch.org/whl/{a.cuda}"])
    reqs = [ln.strip() for ln in (repo / "requirements.txt").read_text().splitlines()
            if ln.strip() and not ln.startswith("#") and not ln.startswith("torch")]
    run(pip + reqs)

    model = home / "model"
    if not (model / "model.safetensors").exists():
        run([py, "-c", f"from huggingface_hub import snapshot_download as s; s({MODEL!r}, local_dir={str(model)!r})"])
    run([py, "-c", "import torchaudio; torchaudio.pipelines.MMS_FA.get_model(); print('aligner ready')"])

    if not a.no_test:
        test = home / "setup_test"
        test.mkdir(exist_ok=True)
        (test / "narration.json").write_text(
            '{"tts": {"engine": "ming", "voice": "US_James", "workers": 1},'
            ' "scenes": [{"id": "test", "lines": ["Ming is installed, and this sentence is the test."]}]}')
        env = {**os.environ, "MING_TTS_HOME": str(home)}
        run([sys.executable, Path(__file__).with_name("tts.py"), test], env=env)
        print(f"Test clip: {test / 'audio' / 'test_0.wav'}")
    print(f"\nMing is ready in {home}." + ("" if str(home) == default else f" Set MING_TTS_HOME={home} for tts.py."))


if __name__ == "__main__":
    main()
