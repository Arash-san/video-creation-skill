![Video Creation header: three frames from the demo video](assets/header.png)

# Video Creation

An AI agent skill for making narrated, animated explainer videos: research to script, a natural voice, a custom visual style, hand-built animation, burned-in subtitles and a finished 1080p MP4.

The skill's main idea is that **every video gets its own art direction.** Most AI-made videos share one tired look: dark background, rounded cards, pill labels, bullets fading in. This skill makes the agent invent a fresh world for each video, such as a risograph zine, a cyanotype light lab, a naturalist's atlas, a transit map or a phosphor oscilloscope. It records each style it uses so the next video looks different.

Watch the 72-second demo, made entirely with this skill: [assets/demo_hash_table_720p.mp4](assets/demo_hash_table_720p.mp4)

## Recommended model

For the best results, use **Claude Opus 5.5** (`claude-opus-5-5`). These videos depend on judgment and craft: inventing a coherent art direction, writing clear narration, choreographing dozens of synchronized animations, and then critiquing its own contact sheets and fixing them. Opus 5.5 does all of this noticeably better than smaller or older models. Other capable agents can run the skill too, but expect more iterations.

## How it works

```
narration.json ──tts.py──▶ voice clips + word timings ──timeline.py──▶ timeline, narration.wav, subtitles
style.js + scenes.js + core.js ──render.py (headless Chromium, parallel)──▶ frames ──assemble.py (ffmpeg)──▶ MP4
```

- Each frame is a pure JavaScript function of time drawn on a 1920x1080 canvas, so the agent controls every pixel and frames render in parallel and in any order.
- Every animation is tied to the narration: `cue.t(k)` is when sentence `k` of a scene starts, so visuals land on the words that explain them.
- `style_roll.py` proposes art directions from a catalog of 30 media, 18 transitions, 7 camera grammars, 10 through-lines, 5 energies and 6 layouts. It always includes one hybrid of two media, and it skips styles you have already used.
- `render.py check` automatically finds overlapping text, text off the frame and text under the subtitles; contact sheets cover the rest.
- Optional generated illustrations are keyed onto the canvas with `key_background.py`.

## Install

```bash
git clone https://github.com/Arash-san/video-creation-skill.git
cd video-creation-skill
pip install -r requirements.txt
python -m playwright install chromium
# ffmpeg and ffprobe must be on PATH (with libass, which most builds include)
```

Use it as a skill:

- **Claude Code:** copy or symlink the folder to `~/.claude/skills/video-creation` (or `.claude/skills/` in a project). Then ask: *"Make a 3 minute explainer video about how TCP congestion control works."*
- **Codex:** copy it to `~/.codex/skills/video-creation`. `agents/openai.yaml` provides the display name and default prompt.
- **Any other agent** that can run shell commands: point it at `SKILL.md`.

## Quick start by hand

```bash
python scripts/new_project.py ../my-video
python scripts/style_roll.py                       # pick a direction, then --record it
# edit ../my-video/narration.json, BRIEF.md, style.js, scenes.js
python scripts/fetch_fonts.py ../my-video "Fraunces" "Outfit" "Space Mono"
python scripts/tts.py ../my-video
python scripts/timeline.py ../my-video
python scripts/render.py ../my-video sheets        # look at stills/*.png
python scripts/render.py ../my-video check
python scripts/render.py ../my-video video
python scripts/assemble.py ../my-video --name my_video --split-mb 50
```

## Repository layout

| Path | What it is |
|------|------------|
| `SKILL.md` | The instructions the agent follows |
| `references/art-direction.md` | How to invent a style, what reads as template, three case studies |
| `references/style_axes.json` | The style catalog used by `style_roll.py` |
| `references/animation.md` | Helper API and animation craft patterns |
| `references/narration.md` | Writing for the ear, honesty rules, `narration.json` format |
| `references/qa.md` | Checklist before and after the full render |
| `references/illustrations.md` | Optional generated illustrations and keying |
| `scripts/` | `new_project`, `style_roll`, `fetch_fonts`, `tts`, `timeline`, `render`, `assemble`, `key_background` |
| `assets/template/` | The engine and stubs copied into each new project |
| `examples/hash-table/` | The full demo project (risograph zine style) |

## Notes

- The default voice is Microsoft Edge's neural TTS through `edge-tts` (free, needs internet). Any voice can be set in `narration.json`.
- Fonts come from the Google Fonts repository under open licenses.
- Rendering runs at about 28 frames per second with 8 workers on a desktop CPU: the demo's 2,147 frames took about 75 seconds.

## License

MIT
