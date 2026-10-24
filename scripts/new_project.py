"""Create a new video project from the template.

    python new_project.py PATH/TO/my-video

Copies assets/template (engine, page, stub scenes, narration and brief) into the new folder.
Next: write BRIEF.md, roll a style (style_roll.py), write narration.json, style.js and scenes.js.
"""
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    dst = Path(sys.argv[1]).resolve()
    if dst.exists() and any(dst.iterdir()):
        raise SystemExit(f"{dst} exists and is not empty; pick a new folder")
    shutil.copytree(SKILL / "assets" / "template", dst, dirs_exist_ok=True)
    for d in ("fonts", "art", "stills"):
        (dst / d).mkdir(exist_ok=True)
    print("created", dst)
    print("files:", ", ".join(sorted(p.name for p in dst.iterdir())))
