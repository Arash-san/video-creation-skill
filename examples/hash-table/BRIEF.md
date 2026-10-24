# Brief: How a hash table finds things in one step (demo)

Audience: programmers and students who use dictionaries or maps but never looked inside one.
Goal: understand hashing, buckets, collisions and resizing well enough to explain why lookups are fast.
Length: about 70 seconds. Sources: standard data-structures material; the hash value 3,204,571 is illustrative.

## Art direction: "Risograph zine"
- World: a two-ink risograph print on off-white stock; each scene is a new sheet fed through the machine.
- Palette: paper #F3EEE3; federal blue #2E4FA3 for all line work and text; fluorescent pink #FF48B0 for the
  thing being searched for or moved; yellow #FFE14D highlighter only for the one takeaway per scene.
- Type: Bricolage Grotesque (display), Space Grotesk (text, subtitles), Space Mono (keys, code, numbers).
- Texture: grain multiplied over everything, paper fibres, faint ink-starved bands, halftone fills,
  pink layer misregistered by a few pixels and settling as each sheet lands.
- Motif / through-line: the row of buckets, which persists from scene 3 to scene 5 and changes size.
- Camera: fixed plates. Transition: "sheet", the next page slides in over the last with a contact shadow.
- Energy: brisk and playful (bounces, a stamp, a seesaw) but readable.

## Scene plan
| id | narration idea | visual argument |
|----|----------------|-----------------|
| title | finding one item among millions | halftone sun ringed by orbiting keys; "Find it in one step." overprinted |
| scan | linear search is slow | pointer crosses out 12 name tiles; row collapses into a million ticks; counter explodes to 1,000,000 |
| hash | hash function → number → bucket | letters of "cat" fly into a shaking hopper; a number prints; % 8 picks bucket 3; item drops in |
| lookup | lookup repeats the same jump | find("cat") jumps straight to bucket 3; table grows 8 → 512 slots while "steps: 1" stays |
| collide | collisions, chaining, resizing | "dog" lands on "cat", bounces, stamp; two-item list; table doubles to 16 and dog moves to 11 |
| outro | trade memory for speed | seesaw tips toward speed; "compute, don't search." with "search" struck out |
