# Inventing an art direction

A video's art direction is the world every frame lives in: a material, a palette with meanings, a type pairing, a texture, a motif that carries the argument, a camera grammar and a way of moving between scenes. Decide it before writing any scene code, write it in `BRIEF.md`, and keep it consistent.

## Why this matters

Most generated videos look the same: a dark navy or black background, rounded translucent cards, pill-shaped labels, a gradient accent, bullet points fading in one after another, maybe a glowing blob. Viewers recognize that look at once and read it as machine-made filler. A distinct, crafted world signals care and makes the explanation memorable.

## Process

1. **Start from the subject, not from a style.** Ask what the topic physically is or feels like. Light through fiber suggests sun prints and glowing threads. Bio-inspired sensors suggest a naturalist's atlas. Hash tables (sorting things into slots) suggest a printed zine with bins. Networking suggests a transit map. History suggests a newspaper. Write three or four associations.

2. **Roll candidates.** `python scripts/style_roll.py --n 4` prints combinations of medium, transition, camera, through-line, energy, layout and narrator voice from `style_axes.json`, skipping media used before (log in `~/.video-creation/styles.jsonl`). The last candidate is always a hybrid of two media, which often produces the most original looks (for example "Transit map x Risograph").

3. **Choose and bend.** Pick the candidate that best matches your associations, or combine one with your own idea. Then adapt:
   - **Palette:** keep 1 background, 1 ink, 2 or 3 accents at most. Give every accent a meaning (for example pink = the thing we are looking for, yellow = what to remember) and never use it for anything else.
   - **Type:** a display face with character for titles, a quiet text face for labels, and a mono or tabular face for numbers. Fetch them with `fetch_fonts.py`. Avoid Inter/Roboto as the display face unless the style is Swiss.
   - **Texture:** paper, grain, scanlines, halftone, glass, felt or none. Build it once in `prep()` and draw it in `overlay()`.
   - **Motif / through-line:** the device that connects scenes (a thread of light, numbered plates, a route map, a running counter). It is what makes ten scenes feel like one film.
   - **Camera:** fixed plates, one continuous world with a flying camera (`withCam`, `camAt`), scrolling, orbiting, or diving into details.
   - **Voice:** cast the narrator to fit the world, the way you chose the palette. A cyanotype light lab might get a calm planetarium guide; a risograph zine a quick, friendly podcast voice; a naturalist's atlas an unhurried documentary narrator. With Ming installed, write it as a `"design"` description in `narration.json` (each candidate from `style_roll.py` suggests one). Vary gender, age, accent and pace between videos as deliberately as the visuals. See [narration.md](narration.md#the-voice).
   - **Transition:** pick one family and use it consistently: built-ins are `cut`, `fade`, `iris`, `wipe`, `sheet`, `zoom`, or write your own `(prev, next, u, i)` function in `style.js` that fits the world (an ink drop that spreads, a page that turns, a CRT that collapses to a dot).

4. **Make a style test before the scenes.** Draw the title scene and one dense scene, render two stills, and ask: *Would this look generic next to a template video? Could someone name the style in three words?* If not, push harder: bigger type, bolder texture, a stranger camera, a stronger motif.

5. **Record it.** `python scripts/style_roll.py --record "<name>" --title "<video>" --notes "<palette, fonts, motif>"` so the next video avoids it.

## Things that read as template or slop (avoid)

- Dark background plus rounded semi-transparent cards plus pill labels
- Bullet lists that fade in line by line; slide-deck layouts with a title and three boxes
- Purple-to-blue gradients, glassmorphism, glowing orbs with no meaning
- Emoji and stock icons as illustration
- Every element centered, same size, same easing
- A lime-on-black "terminal" theme by default
- Random decoration (floating particles, lines, dots) that does not explain anything

## What strong directions have in common

- One clear material metaphor that the animation exploits (ink overprints, light glows, paper folds, glass fills with light).
- Type treated as image: large, confident, sometimes cropped, with real hierarchy.
- Imperfection from the medium: misregistration, grain, jitter, hand-drawn strokes (`jitter()`, `underline()`), never sterile vectors unless the style is precise by design.
- The motif doing explanatory work, not decoration.

## Case studies

**Cyanotype light lab** (a paper on imaging through optical fibers). Prussian-blue sun-print paper with fiber grain, cream line art, and one warm amber thread of light that runs through the entire video. The camera rides a pulse of light from station to station along the thread; in the second half the thread becomes a radiation beam. Fonts: Instrument Serif, IBM Plex Sans Condensed, IBM Plex Mono.

**Naturalist's atlas** (bio-inspired sensors modelled on bird eyes, bee vision and skin). Cream plate paper, sepia engraving ink, hand-tinted teal, vermilion and ochre; each scene is a numbered plate with a roman numeral; engraved animal illustrations generated by an image model and keyed onto the paper. Scenes open like a pupil dilating. Fonts: Cormorant Garamond, Work Sans, DM Mono.

**Risograph zine** (the demo in `examples/hash-table`). Off-white stock, federal blue and fluorescent pink inks that overprint with multiply blending and misregister by a few pixels, a yellow highlighter ink reserved for the one thing to remember per scene, halftone fills, grain and ink-starved bands. New sheets slide in like a duplicator feeding paper. Fonts: Bricolage Grotesque, Space Grotesk, Space Mono.

Notice that none of the three shares a palette, typeface, texture or transition.
