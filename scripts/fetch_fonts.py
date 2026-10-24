"""Download Google Fonts families (open licenses) into a project's fonts/ folder.

    python fetch_fonts.py PROJECT_DIR "Bricolage Grotesque" "Space Mono" ...

Files come from the github.com/google/fonts repository, so no API key is needed.
Prints an @font-face block you can paste into index.html.
Variable fonts also get static copies (weights 400-700) in fonts/subs/, because the subtitle
renderer (libass) cannot use variable fonts and silently falls back to Arial. Needs fonttools.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

API = "https://api.github.com/repos/google/fonts/contents/{lic}/{slug}"
RAW = "https://raw.githubusercontent.com/google/fonts/main/{lic}/{slug}/{name}"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "video-creation-skill"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def static_copies(var_path, family, dst):
    try:
        from fontTools.ttLib import TTFont
        from fontTools.varLib import instancer
    except ImportError:
        print("  (pip install fonttools to get static subtitle fonts)", file=sys.stderr)
        return
    dst.mkdir(exist_ok=True)
    axes = {a.axisTag: a for a in TTFont(var_path)["fvar"].axes}
    if "wght" not in axes:
        return
    for w in (400, 500, 600, 700):
        if not axes["wght"].minValue <= w <= axes["wght"].maxValue:
            continue
        target = dst / f"{family.replace(' ', '')}-{w}.ttf"
        if target.exists():
            continue
        f = TTFont(var_path)
        loc = {t: (w if t == "wght" else a.defaultValue) for t, a in axes.items()}
        st = instancer.instantiateVariableFont(f, loc)
        # name the instance by hand: same family, weight in OS/2, so libass picks it for Bold=0/-1
        sub = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"}[w]
        nm = st["name"]
        for rec in list(nm.names):
            if rec.nameID in (16, 17, 25):
                nm.removeNames(nameID=rec.nameID)
        nm.setName(family, 1, 3, 1, 0x409)
        nm.setName("Bold" if w == 700 else "Regular", 2, 3, 1, 0x409)
        nm.setName(f"{family} {sub}", 4, 3, 1, 0x409)
        nm.setName(f"{family.replace(' ', '')}-{sub}", 6, 3, 1, 0x409)
        st["OS/2"].usWeightClass = w
        st.save(target)


def fetch(family, out):
    slug = re.sub(r"[^a-z0-9]", "", family.lower())
    for lic in ("ofl", "apache", "ufl"):
        try:
            items = json.loads(get(API.format(lic=lic, slug=slug)))
        except Exception:
            continue
        ttfs = [i["name"] for i in items if i["name"].endswith(".ttf")]
        if not ttfs:
            continue
        # prefer variable fonts ("[wght]"), else every static weight
        var = [n for n in ttfs if "[" in n]
        chosen = var or ttfs
        faces = []
        for n in chosen:
            local = n.replace("[", "_").replace("]", "_").replace(",", "_")
            p = out / local
            if not p.exists():
                p.write_bytes(get(RAW.format(lic=lic, slug=slug, name=n)))
            italic = "Italic" in n
            if "[" in n and not italic:
                static_copies(p, family, out / "subs")
            if "[" in n:
                weight = "100 900"
            else:
                m = re.search(r"-(Thin|ExtraLight|Light|Regular|Medium|SemiBold|Bold|ExtraBold|Black)", n)
                weight = {"Thin": 100, "ExtraLight": 200, "Light": 300, "Regular": 400, "Medium": 500,
                          "SemiBold": 600, "Bold": 700, "ExtraBold": 800, "Black": 900}.get(m.group(1) if m else "Regular", 400)
            faces.append(f'@font-face{{font-family:"{family}";src:url(fonts/{local});'
                         f'font-style:{"italic" if italic else "normal"};font-weight:{weight}}}')
        return faces
    raise SystemExit(f"not found in google/fonts: {family} (slug {slug})")


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]) / "fonts"
    out.mkdir(parents=True, exist_ok=True)
    css = []
    for fam in sys.argv[2:]:
        css += fetch(fam, out)
        print("ok", fam, file=sys.stderr)
    print("\n".join(css))


if __name__ == "__main__":
    main()
