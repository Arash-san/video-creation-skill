"""Turn the flat background of generated illustrations into transparency.

    python key_background.py art/plate1.png art/plate2.png ...

Writes <name>_a.png next to each input: alpha comes from the distance to the border colour,
colours are un-premultiplied so inks keep their strength, and the result is cropped to content.
Works best when the image model was asked for "isolated on a plain flat <colour> background".
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def key(p, lo=10, span=55):
    im = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    h, w, _ = im.shape
    border = np.concatenate([im[:12].reshape(-1, 3), im[-12:].reshape(-1, 3),
                             im[:, :12].reshape(-1, 3), im[:, -12:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    d = np.sqrt(((im - bg) ** 2).sum(-1))
    a = np.clip((d - lo) / span, 0, 1)
    out = np.where(a[..., None] > 0.02, (im - bg * (1 - a[..., None])) / np.maximum(a[..., None], 0.02), im)
    rgba = np.dstack([np.clip(out, 0, 255), a * 255]).astype(np.uint8)
    ys, xs = np.where(a > 0.08)
    if len(ys) == 0:
        raise SystemExit(f"{p}: nothing left after keying (is the subject the same colour as the background?)")
    y0, y1 = max(0, ys.min() - 20), min(h, ys.max() + 20)
    x0, x1 = max(0, xs.min() - 20), min(w, xs.max() + 20)
    dst = p.with_name(p.stem + "_a.png")
    Image.fromarray(rgba[y0:y1, x0:x1]).save(dst)
    print(f"{p.name}: background {bg.round().astype(int).tolist()}, cropped to {x1 - x0}x{y1 - y0} -> {dst.name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for arg in sys.argv[1:]:
        key(Path(arg))
