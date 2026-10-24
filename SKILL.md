---
name: video-creation
description: Create narrated, animated explainer videos (1080p MP4 with a voice track and burned-in subtitles) from a topic, paper, codebase, dataset or notes. Frames are drawn in code on an HTML canvas, rendered in headless Chromium and assembled with ffmpeg. Every video gets its own invented art direction instead of a template look. Use when asked to make an explainer video, animated video, narrated walkthrough, research or paper summary video, lecture animation, or "a video about X".
---

# Video Creation

You make a complete narrated video: research, script, voice, a custom visual style, hand-built animation, subtitles, and a finished MP4. The engine is small and transparent: each frame is a pure JavaScript function of time drawn on a 1920x1080 canvas, so you control every pixel and can render frames in parallel.

The most important rule: **every video must look like nobody has made it before.** Do not reuse a previous video's palette, fonts, textures, layout or transitions, and never fall back on the generic "dark background, rounded cards, pill labels, bullets fading in" look. See [references/art-direction.md](references/art-direction.md).

## Requirements

- Python 3.10+ with `pip install -r requirements.txt` (edge-tts, numpy, pillow, playwright, fonttools)
- `python -m playwright install chromium`
- `ffmpeg` and `ffprobe` on PATH, built with libass (most builds are)
- Internet access for the voice (edge-tts) and fonts (Google Fonts via GitHub)

All commands below run from this skill folder; `PROJ` is the project folder you create.

## Workflow

1. **Understand the material.** Read the sources fully. Write down the audience (what they already know and what they do not), the one thing they should leave with, and every number you will show with its source. Never invent figures.

2. **Create the project.**
   `python scripts/new_project.py PROJ`
   This copies the engine (`core.js`, `main.js`, `index.html`) and stubs (`style.js`, `scenes.js`, `narration.json`, `BRIEF.md`).

3. **Invent the art direction.** Run `python scripts/style_roll.py` to get four candidate directions combined from a large catalog (media, transitions, camera, through-lines, energy, layout). Styles you used before are skipped automatically. Pick the one that fits the topic best, then push it further: change the palette to suit the subject, choose a motif that carries the argument, and decide how scenes connect. You may also invent something outside the catalog entirely. Fill in the art direction section of `PROJ/BRIEF.md`, then record the choice:
   `python scripts/style_roll.py --record "<style name>" --title "<video>" --notes "<palette, type, motif>"`

4. **Write the narration** in `PROJ/narration.json`: scenes, each with a list of spoken lines. Follow [references/narration.md](references/narration.md). Plan each scene's visual argument next to its lines in `BRIEF.md` (what animates while each sentence is spoken).

5. **Synthesize the voice and timeline.**
   `python scripts/tts.py PROJ` then `python scripts/timeline.py PROJ`
   This writes the audio, `timeline.json` (when each scene and line starts), `narration.wav` and `subs.ass`. Only changed lines are re-synthesized, so rerun both after any text edit.

6. **Fetch fonts** for your direction: `python scripts/fetch_fonts.py PROJ "Display Family" "Text Family" "Mono Family"`, then paste the printed `@font-face` lines into `PROJ/index.html`. Set the subtitle font in `narration.json` to one of these families.

7. **Write `style.js`**: `STYLE` (fonts, transition), the palette `C`, and the `background()` / `overlay()` painters (paper, grain, light, frame chrome). Add style-specific helpers here, such as an ink pass, a glow, a hatching or a halftone. The demo in [examples/hash-table](examples/hash-table) shows a complete style.

8. **Write `scenes.js`**: one `SC[id] = (lt, cue) => {...}` per scene. Tie every reveal to the narration with `cue.t(k)` (start of line k). Read [references/animation.md](references/animation.md) for the helper API and the craft patterns.

9. **Look, check, fix, repeat.** This is where quality comes from.
   - `python scripts/render.py PROJ sheets` draws a contact sheet per scene into `PROJ/stills/`. Open them and look.
   - `python scripts/render.py PROJ check` reports overlapping text, text off the frame, and text in the subtitle band.
   - `python scripts/render.py PROJ stills 12.5 40` renders exact moments at full size.
   Go through [references/qa.md](references/qa.md) before the full render.

10. **Render and assemble.**
    `python scripts/render.py PROJ video` renders all frames in parallel chunks (resumable; delete `PROJ/chunks` to start over).
    `python scripts/assemble.py PROJ --name my_video` writes `PROJ/deliverables/my_video_1080p.mp4` with voice and burned-in subtitles. Add `--split-mb 50` to also cut parts that each fit an upload cap, split at scene boundaries.

11. **Verify the output** by extracting a few frames from the final MP4 with ffmpeg (check subtitles and fonts) and confirming the duration matches the timeline. Report the file path, duration and size.

## Rules

- **Fresh art direction every time.** Pick it deliberately with `style_roll.py`, log it, and never repeat a past direction for the same user.
- **Animation carries the explanation.** Diagrams that build, morph, move and transform while the sentence explains them. A scene that only fades text in has failed.
- **Synchronize to speech.** Each visual change starts within about half a second of the words that describe it. Use `cue.t(k)` plus an offset, never absolute guesses.
- **Frames are pure functions of time.** No state carried between frames, no `Math.random()` (use `rng(seed)`), no `Date.now()`. Chunks render in separate browsers and out of order.
- **Keep content above the subtitle band** (`SAFE_BOTTOM`, y = 900 by default) and inside a 24 px margin.
- **Accuracy over flourish.** Every number, label and claim on screen must come from the sources. Say "illustrative" on screen when a chart is a sketch rather than data.
- **No mascots, music or sound effects** unless the user asks for them. Default voice is a natural female neural voice (`en-US-AvaMultilingualNeural`); change it in `narration.json` if the user prefers.

## Optional: generated illustrations

When a style needs rich illustration (engraved plates, painted scenes, objects), generate images with whatever image model is available, ask for the subject "isolated on a plain flat <paper colour> background", then key the background out with `python scripts/key_background.py PROJ/art/*.png` and draw them with `plate()`. See [references/illustrations.md](references/illustrations.md).

## Known traps

- **Subtitle font falls back to Arial:** libass cannot use variable fonts. `fetch_fonts.py` writes static copies to `fonts/subs/` and `assemble.py` uses them. Static instances often run smaller than the variable font did, so check the size on a real frame.
- **"Tainted canvas" / `toDataURL` SecurityError:** images loaded from `file://` need the Chromium flags in `render.py` and `crossOrigin = 'anonymous'` (already in `loadArt`).
- **Fonts silently missing in frames:** `boot()` loads every weight before setting `READY`; a family name that does not match the `@font-face` name falls back to a system font. Compare a still against the intended face.
- **edge-tts "No audio was received":** transient; `tts.py` retries. If one line keeps failing, rephrase odd characters.
- **Slow renders:** each worker runs its own Chromium. Heavy per-frame work (big textures, thousands of dots) belongs in `prep()` or a cached canvas. Workers default to half the CPU cores.
- **Huge files:** grain and noise textures make video bitrates large. `assemble.py --split-mb` applies a light denoise before encoding the parts.
