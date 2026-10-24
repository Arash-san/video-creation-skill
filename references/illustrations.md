# Generated illustrations (optional)

Canvas drawing handles diagrams, type and abstract shapes well. Some styles need real illustration: engraved animals, painted landscapes, detailed objects. Generate those as images and composite them as "plates".

## Generating

Use whichever image model you have access to (for example GPT Image, Imagen, Flux or Stable Diffusion). For an agent with the Codex CLI, the [codex-imagegen-sdk](https://github.com/Arash-san/codex-imagegen-sdk) skill drives image generation from code.

Prompt pattern:

```
<subject>, drawn as <medium of the art direction> (for example: a 19th-century copperplate engraving
with fine hatching, sepia ink, hand-tinted with teal and vermilion washes). Isolated on a plain flat
cream (#EFE6D2) background, no border, no text, no frame, no shadow on the background,
the subject centred with generous empty margin.
```

- Ask for the same medium, inks and line weight in every prompt so the plates match each other and the canvas.
- Ask for **no text**: image models misspell labels. Add labels on the canvas instead, with leader lines.
- Generate one or two extra candidates per plate and pick the best. Check each image for invented details (wrong anatomy, extra logos, landmarks you did not ask for).
- Store prompts in `art/prompts/<name>.txt` so plates can be regenerated.

## Keying and using

```
python scripts/key_background.py PROJ/art/kingfisher.png PROJ/art/bee.png
```

This writes `kingfisher_a.png` with the flat background turned into transparency (alpha from the distance to the border color, colors un-premultiplied, cropped to content). Then:

```js
// style.js
STYLE.art = ['kingfisher', 'bee'];
// scenes.js
plate('kingfisher', 1300, 480, 620, E.out(P(lt, cue.t(0), 1.0)));
```

Animate plates the way the medium would: an engraving can be revealed by a sweeping clip (`{clip: () => ctx.rect(...)}`), a watercolor can bloom with a growing soft mask, a cut-paper piece can slide in with a shadow. Avoid simply fading a picture in and leaving it static; add a slow drift, a scale breath, or labels that draw in around it.
