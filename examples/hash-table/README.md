# Demo: hash tables in a risograph zine style

A complete 65-second project made with this skill, narrated by a Ming-3.0-tts voice designed to fit the zine (see the `tts` block in `narration.json`). Preview: [../../assets/demo_hash_table_720p.mp4](../../assets/demo_hash_table_720p.mp4)

Rebuild it from this folder's parent (the skill root):

```bash
python scripts/fetch_fonts.py examples/hash-table "Bricolage Grotesque" "Space Grotesk" "Space Mono"
python scripts/tts.py examples/hash-table
python scripts/timeline.py examples/hash-table
python scripts/render.py examples/hash-table check
python scripts/render.py examples/hash-table video
python scripts/assemble.py examples/hash-table --name hash_table_demo
```

Files to read: `BRIEF.md` (the art direction and scene plan), `narration.json`, `style.js` (palette, ink passes,
halftone, misregistration) and `scenes.js` (six scenes). `core.js`, `main.js` and `index.html` are the template engine.
