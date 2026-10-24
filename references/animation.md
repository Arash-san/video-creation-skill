# Animation craft and helper API

## The model

`renderFrame(T)` finds the scene at time `T`, calls `background(i, lt)`, then `SC[id](lt, cue)`, then `overlay(i, lt)`. During the first `STYLE.transitionDur` seconds of a scene, the transition draws both the outgoing scene (still animating past its end) and the incoming one.

Inside a scene everything is computed from `lt` (seconds since the scene began). The usual building block is a progress value:

```js
const u = E.out(P(lt, cue.t(1) + 0.4, 0.8));   // 0 -> 1 over 0.8 s, starting 0.4 s after line 1 begins
```

- `P(t, start, dur)`: linear progress clamped to 0..1
- `E.out`, `E.out5`, `E.io`, `E.in`, `E.back`, `E.elastic`: easings
- `span(t, a, b, fade)`: rises after `a`, falls before `b` (for things that appear and leave)
- `lerp`, `clamp`, `smooth`, `rng(seed)` (deterministic random), `noise1(x, seed)`

## Cues

`cue.t(k)` start of narration line `k` in this scene, `cue.e(k)` its end, `cue.d` scene length, `cue.n` number of lines. Word-level timing lives in `audio/<scene>_<k>.words.json` if you need to land a reveal on one specific word: open the file, find the word's start in seconds, and use `cue.t(k) + that`.

## Helpers (core.js)

Text:
- `tx(s, x, y, {size, w, fam, it, c, a, al, bl, tr, glow, stroke, noCheck})` draws text. `fam` is `DISPLAY`, `TEXT` or `MONO`; `al` alignment; `tr` letter spacing; `a` alpha.
- `rise(s, x, y, o, lt, t0, stagger, dur)` words rise in one by one; wrap words in `*asterisks*` to set them italic in `o.itc`.
- `para(s, x, y, maxw, lineHeight, o, lt, t0)` wrapped paragraph that rises line by line.
- `typed(s, x, y, o, u)` typewriter with a cursor. `num(s, x, y, o)` fixed-width digits for proportional fonts (counters that do not jitter). `fmtInt(v)` adds thousands separators.
- `tw(s, o)` measures width; `wrap(s, maxw, o)` returns lines.

Strokes and shapes:
- `poly(points, u, col, lw, {dash, a, comp, from})` draws the first `u` of a polyline and returns the pen position; this is the core of "drawn" animation.
- `qpts`, `arcPts` build curves as point lists; `jitter(points, amp, seed)` makes them hand-drawn.
- `line`, `arrow(x1, y1, x2, y2, u)`, `carrow` (curved), `head`, `circle({u})` (partial arcs), `rect`, `rectDraw(x, y, w, h, u)`, `underline`.
- `hatch(pathFn, angle, gap, col)` engraved fill; `glow(x, y, r, col)` additive light.

Camera and images:
- `withCam({x, y, z, r}, fn)` draws a world through a camera; `camAt(t, [[t0, {x, y, z}], ...])` interpolates camera keyframes (zoom interpolates in log space so it feels even).
- `plate(name, x, y, width, alpha, {clip, comp})` draws a keyed illustration from `art/<name>_a.png` (list names in `STYLE.art`).
- `clipCircle`, `mkCanvas`, `grainTexture`, `tile(texture, seed, alpha, comp)`, `vignette`.

Put style-specific helpers (ink passes, halftones, glows, specific frames) in `style.js`, as the demo does.

## Patterns that look crafted

- **Draw, do not fade.** Lines, arrows, outlines and diagrams should be drawn with `poly(..., u)` along their length. Fades are for text and secondary elements.
- **Build the diagram while it is explained.** One part per clause of the sentence. If the narration says "the key goes through a hash function, which turns it into a number", show the key, then the function, then the number, each on its words.
- **Morph rather than replace.** When a concept becomes another (12 tiles become a million ticks; 8 buckets become 16), interpolate positions, sizes and counts so the eye follows the change.
- **Counters and meters** for quantities: animate the number with an easing that matches the meaning (`E.in` for explosive growth).
- **Camera with purpose:** push in to the detail being discussed, pull out to show context. Ease every move (`E.io`), and keep moves under about 2 seconds.
- **Stagger.** Groups enter with 40 to 120 ms offsets, not all at once.
- **Overshoot sparingly.** `E.back` for things that land or snap into place, not for everything.
- **Hold.** After a build completes, let it sit while the voice finishes; viewers need time to read.
- **Continuity.** Elements that persist from scene to scene should sit in the same place, so transitions feel like one world.
- **One focal point at a time.** Dim or shrink what is no longer being discussed.

## Layout

- Canvas is 1920x1080. Keep a 90 px outer margin for chrome, content above `SAFE_BOTTOM` (900 by default) because subtitles sit below.
- Headline sizes 64 to 150 px, labels 24 to 36 px, nothing under 20 px (it disappears after compression).
- Use a grid: define column x positions once per scene and place everything on them.

## Performance

Per frame, keep work modest: a few thousand path segments is fine; tens of thousands of dots per frame will slow rendering. Precompute textures, point lists and layouts in `prep()` and cache canvases. Avoid `shadowBlur` on many objects; stack a few wide translucent strokes instead.
