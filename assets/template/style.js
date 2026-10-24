// style.js: the art direction for THIS video. Replace everything here for every new video;
// never reuse a previous video's palette, fonts, textures or transition. See references/art-direction.md.
'use strict';
const STYLE = {
  name: 'REPLACE ME',
  fonts: { display: 'Georgia', text: 'Arial', mono: 'Courier New' },   // real families via fetch_fonts.py
  transition: 'fade',          // cut | fade | iris | wipe | sheet | zoom | or your own function(prev, next, u, i)
  transitionDur: 1.2,
  art: [],                     // names of art/<name>_a.png plates to preload (see key_background.py)
};
const C = {
  bg: '#EEEEEE',               // page colour (the 'sheet' transition also uses it)
  ink: '#222222',              // main line and text colour
  ink2: 'rgba(34,34,34,0.65)', // secondary text
  ink3: 'rgba(34,34,34,0.30)', // hairlines, grids
  a1: '#CC3333', a2: '#3366CC', a3: '#DDAA22',   // accents: give each one a meaning and keep it
};
let GRAIN = null;
async function prep() { GRAIN = grainTexture(7, [0, 0, 0], 20); }
// paints the whole frame behind the scene; i = scene index, lt = scene time
function background(i, lt) { ctx.fillStyle = C.bg; ctx.fillRect(0, 0, W, H); }
// drawn on top of every scene: grain, vignette, frame chrome, running header
function overlay(i, lt) { tile(GRAIN, i, 1); }
