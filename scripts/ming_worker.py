"""Ming-3.0-tts worker. tts.py runs this inside the Ming environment; you do not call it directly.

    <ming venv python> ming_worker.py JOB.json

JOB.json: {"repo", "model", "device", "voice": {...}, "anchor_dir", "lines": [{"key", "text", "wav", "words", "meta", "sig"}]}

For each line it writes a 48 kHz mono WAV and word timings ([start, end, word], seconds) found by
forced alignment (torchaudio MMS_FA) against the known text, so subtitles and cues stay in sync.
"""
import hashlib
import json
import os
import re
import sys
import time

TAG = re.compile(r"\[[A-Za-z][A-Za-z-]*\]")  # inline paralinguistic tags such as [Laughter]
OUT_SR = 48000
MATCH_MIN = 0.15  # lowest per-word alignment confidence for a line to count as matching the script
VOICE_MIN = 0.65  # lowest speaker similarity to the anchor (same-voice lines measure 0.75 to 0.93)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def seed_for(text):
    return int(hashlib.sha1(text.encode()).hexdigest()[:8], 16)


class Aligner:
    """Forced alignment of known English text with torchaudio's MMS_FA model."""

    def __init__(self, device, normalize_numbers):
        import torchaudio
        self.ta = torchaudio
        self.bundle = torchaudio.pipelines.MMS_FA
        self.model = self.bundle.get_model(with_star=False).to(device).eval()
        self.dictionary = self.bundle.get_dict(star=None)
        self.device = device
        self.norm_numbers = normalize_numbers

    def pieces(self, word):
        """Letters the aligner can use for one written word (numbers are spelled out first)."""
        spoken = self.norm_numbers(word) if re.search(r"\d", word) else word
        spoken = spoken.lower().replace("’", "'")
        return [p for p in (re.sub(r"[^a-z']", "", s) for s in re.split(r"[\s-]+", spoken)) if p]

    def align(self, wave, sr, text, scores=False):
        """[[start, end, word], ...]; with scores=True each entry also gets the mean letter confidence."""
        import torch
        words = [w for w in TAG.sub(" ", text).split() if w.strip()]
        groups = [(w, self.pieces(w)) for w in words]
        flat = [p for _, ps in groups for p in ps if all(c in self.dictionary for c in p)]
        if not flat:
            return []
        x = self.ta.functional.resample(wave, sr, self.bundle.sample_rate).to(self.device)
        with torch.inference_mode():
            emission, _ = self.model(x)
        tokens = [[self.dictionary[c] for c in p] for p in flat]
        spans = self._spans(emission, tokens)
        ratio = x.shape[-1] / emission.shape[1] / self.bundle.sample_rate
        out, k = [], 0
        for w, ps in groups:
            ps = [p for p in ps if all(c in self.dictionary for c in p)]
            if not ps:
                continue
            seg = spans[k:k + len(ps)]
            k += len(ps)
            row = [round(seg[0][0].start * ratio, 3), round(seg[-1][-1].end * ratio, 3), w]
            if scores:
                letters = [s.score for piece in seg for s in piece]
                row.append(round(sum(letters) / len(letters), 3))
            out.append(row)
        return out

    def _spans(self, emission, tokens):
        import torch
        F = self.ta.functional
        targets = torch.tensor([[t for ws in tokens for t in ws]], dtype=torch.int32, device=emission.device)
        ali, scores = F.forced_align(emission, targets, blank=0)
        ali, scores = ali[0], scores[0].exp()
        spans = F.merge_tokens(ali, scores)
        out, i = [], 0
        for ws in tokens:
            out.append(spans[i:i + len(ws)])
            i += len(ws)
        return out


def main(job_path):
    job = json.load(open(job_path, encoding="utf-8"))
    sys.path.insert(0, job["repo"])
    os.chdir(job["repo"])
    import torch
    import torchaudio
    from ming_tts import MingTTS
    from frontend.number_en import normalize_numbers

    t0 = time.time()
    tn = job.get("text_normalization", False)
    tts = MingTTS(job["model"], device=job.get("device", "cuda:0"), text_normalization=tn)
    aligner = Aligner(job.get("device", "cuda:0"), normalize_numbers)
    log(f"ming: loaded in {time.time() - t0:.1f}s on {torch.cuda.get_device_name(0)}")

    voice = job["voice"]
    lang = voice.get("language")
    base = dict(cfg=voice.get("cfg", 2.0), sigma=voice.get("sigma", 0.25), temperature=voice.get("temperature", 0.0))
    if lang:
        base["language_id"] = lang

    def say(text, attempt=0, **kw):
        torch.manual_seed(seed_for(text + json.dumps(voice, sort_keys=True)) + attempt)
        if not tn and not lang:
            text = normalize_numbers(text)  # pynini is optional; spell out numbers ourselves
        w = tts.synthesize(text=text, **base, **kw)
        return w.float().cpu()

    # One fixed speaker for the whole video. Voice design invents a new speaker on every call and
    # built-in voices drift a little from line to line, so both first make one anchor clip
    # (audio/voice_anchor.wav) and every line clones it.
    mode = voice["mode"]
    if mode == "builtin":
        make = dict(task="IP", controls={"ip": voice["name"]}, use_zero_spk_emb=True)
    elif mode == "design":
        make = dict(task="VOICE_DESIGN", controls={"style": voice["design"]}, use_zero_spk_emb=True)
    elif mode != "clone":
        raise SystemExit(f"unknown voice mode {mode}")
    if mode == "builtin" and not voice.get("lock", True):
        kw = make
    else:
        if mode == "clone":
            ref, ref_text = voice["clone"], voice["clone_text"]
        else:
            ref, ref_text = os.path.join(job["anchor_dir"], "voice_anchor.wav"), voice["anchor_text"]
            sig = hashlib.sha1(json.dumps([make, ref_text, base]).encode()).hexdigest()
            sig_path = ref + ".sig"
            if not (os.path.exists(ref) and os.path.exists(sig_path) and open(sig_path).read() == sig):
                w = say(ref_text, **make)
                torchaudio.save(ref, w, tts.sample_rate)
                open(sig_path, "w").write(sig)
                log(f"ming: made voice anchor ({w.shape[-1] / tts.sample_rate:.1f}s) -> {ref}")
        kw = dict(task="TTS", prompt_wav_path=ref, prompt_text=ref_text, use_spk_emb=True)

    # Automatic listening check, since the agent cannot hear the audio: every line must match the
    # script (forced-alignment confidence of each word) and sound like the anchor (speaker similarity).
    # A line that fails is regenerated with a new seed, up to `retries` times, and the best take is kept.
    ref_emb = None
    if kw["task"] == "TTS":
        ref_emb = speaker(tts, *load_wave(torchaudio, kw["prompt_wav_path"]))
    retries = int(job.get("retries", 2))
    report = []
    total_audio = 0.0
    for ln in job["lines"]:
        t = time.time()
        best = None
        for attempt in range(retries + 1):
            w = say(ln["text"], attempt=attempt, **kw)
            tempo = job.get("tempo", 1.0)
            if abs(tempo - 1.0) > 1e-3:
                w = _atempo(w, tts.sample_rate, tempo)
            scored = aligner.align(w, tts.sample_rate, ln["text"], scores=True)
            # The aligner was trained without digits, so spoken numbers score near zero: skip them.
            checked = [r for r in scored if not re.search(r"\d", r[2])]
            weak = [r[2] for r in checked if r[3] < MATCH_MIN]
            sim = None if ref_emb is None else round(float(speaker(tts, w, tts.sample_rate) @ ref_emb), 3)
            ok = not weak and (sim is None or sim >= VOICE_MIN)
            rank = (ok, -len(weak), sim or 0)
            if best is None or rank > best[0]:
                best = (rank, w, scored, weak, sim, attempt)
            if ok:
                break
        (ok, _, _), w, scored, weak, sim, attempt = best
        words = [r[:3] for r in scored]
        out = torchaudio.functional.resample(w, tts.sample_rate, OUT_SR)
        torchaudio.save(ln["wav"], out, OUT_SR, encoding="PCM_S", bits_per_sample=16)
        json.dump(words, open(ln["words"], "w", encoding="utf-8"))
        open(ln["meta"], "w").write(ln["sig"])
        dur = w.shape[-1] / tts.sample_rate
        total_audio += dur
        report.append({"key": ln["key"], "ok": ok, "take": attempt, "voice_similarity": sim, "unclear_words": weak})
        note = "" if ok else f"  CHECK: unclear {weak}" if weak else f"  CHECK: voice similarity {sim}"
        log(f"ming: {ln['key']} {dur:.1f}s audio in {time.time() - t:.1f}s, take {attempt + 1}, "
            f"voice {sim if sim is not None else '-'}{note}")
    json.dump(report, open(job["report"], "w", encoding="utf-8"), indent=1)
    log(f"ming: {len(job['lines'])} lines, {total_audio:.1f}s audio in {time.time() - t0:.1f}s")


def load_wave(torchaudio, path):
    w, sr = torchaudio.load(path)
    return w.mean(0, keepdim=True), sr


def speaker(tts, w, sr):
    """Unit-length CAM++ speaker embedding (the model's own speaker encoder)."""
    import numpy as np
    import torchaudio
    w16 = torchaudio.functional.resample(w.float().cpu(), sr, 16000)
    e = np.asarray(tts.spkemb_extractor(w16), dtype=np.float32).reshape(-1)
    return e / np.linalg.norm(e)


def _atempo(w, sr, tempo):
    """Change speed without changing pitch, through ffmpeg's atempo filter."""
    import subprocess
    import numpy as np
    import torch
    pcm = (w.clamp(-1, 1).numpy()[0] * 32767).astype(np.int16).tobytes()
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-",
                        "-filter:a", f"atempo={tempo}", "-f", "s16le", "-"], input=pcm, capture_output=True, check=True)
    return torch.from_numpy(np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32767).unsqueeze(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
