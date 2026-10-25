# Quality checklist

Run through this with contact sheets (`render.py PROJ sheets`) and full-size stills before the final render, and again on frames extracted from the finished MP4.

## Automated

- [ ] `python scripts/render.py PROJ check` reports no issues (text overlap, text off frame, text in the subtitle band). Use `noCheck: true` only for text that overlaps on purpose (an ink overprint, a letter in flight).
- [ ] No `PAGE ERRORS` printed by `render.py`, no `*.err` files in `chunks/`.
- [ ] `timeline.py` reports a sensible total and no cue longer than `max_chars`.

## Look at every contact sheet

- [ ] The art direction is visible in every scene: the texture, palette and type are consistent, and nothing looks like a default slide.
- [ ] Shapes, images and lines do not collide with text or with each other (the automated check only sees text).
- [ ] Nothing important is cropped by the frame edge; nothing sits under the subtitles.
- [ ] Each scene has a clear focal point and visible hierarchy.
- [ ] Text is at least 20 px and readable against its background.
- [ ] Colors keep their meanings throughout.

## Watch the timing

- [ ] Render stills at the moments key words are spoken (`render.py PROJ stills T ...`) and confirm the matching visual is already on screen or arriving.
- [ ] Nothing important appears during the first second of a scene, while the transition is still covering it.
- [ ] Transitions look right mid-way (render a still 0.5 s into a scene).

## Content

- [ ] Every number on screen matches the sources and the narration.
- [ ] Names, titles and attributions are correct.
- [ ] Caveats are present where the evidence is limited.

## Voice

- [ ] `tts.py` reports that the listening check passed (`audio/voice_report.json`). For a line that still fails, rephrase it (spell out an awkward name, split a long sentence) and rerun.
- [ ] The voice anchor (`audio/voice_anchor.wav`) fits the art direction. If you can play audio, listen to it and to one full line; otherwise check its length and that the report shows high voice similarity on every line.
- [ ] Inline sound tags such as `[Laughter]` are rare and placed where a person would really make that sound.

## Output

- [ ] Extract two or three frames from the final MP4: subtitles use the intended font (not Arial), sit in the band, and do not cover content.
- [ ] Audio and video durations match; the voice is in sync at the end of the video, not only the start.
- [ ] File size suits the destination; use `--split-mb` for capped uploads.
