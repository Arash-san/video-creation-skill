// style.js (demo): "Risograph zine". Off-white stock, two spot inks (federal blue + fluorescent pink)
// that overprint with multiply, misregister by a few pixels, and carry grain. A yellow highlighter ink
// appears only for the one thing the viewer must remember in each scene.
'use strict';
const STYLE = {
  name: 'Risograph zine',
  fonts: { display: 'Bricolage Grotesque', text: 'Space Grotesk', mono: 'Space Mono' },
  transition: 'sheet',          // a fresh sheet feeds in over the last one, like a duplicator
  transitionDur: 1.1,
  art: [],
};
const C = {
  bg: '#F3EEE3', ink: '#2E4FA3', ink2: 'rgba(46,79,163,0.72)', ink3: 'rgba(46,79,163,0.28)',
  pink: '#FF48B0', pinkS: 'rgba(255,72,176,0.35)', yellow: '#FFE14D',
};
const ISSUE = 'HASH TABLES  ·  A TWO-INK ZINE';
let GRAIN = null, FIBRE = null, REG = { pink: [0, 0], yellow: [0, 0] }, SCENE_I = 0;

async function prep() {
  GRAIN = grainTexture(11, [30, 40, 90], 34);
  FIBRE = mkCanvas(1024, 1024);
  const g = FIBRE.getContext('2d'), r = rng(5);
  for (let k = 0; k < 900; k++) {   // paper fibres
    let x = r() * 1024, y = r() * 1024, a = r() * Math.PI * 2;
    g.strokeStyle = `rgba(120,100,70,${0.04 + r() * 0.06})`; g.lineWidth = 0.6; g.beginPath(); g.moveTo(x, y);
    for (let s = 0; s < 4; s++) { a += (r() - 0.5); x += Math.cos(a) * 6; y += Math.sin(a) * 6; g.lineTo(x, y); }
    g.stroke();
  }
}

// misregistration: each sheet lands slightly off, and the pink drum settles in the first second
function setReg(i, lt) {
  const r = rng(i * 31 + 3), settle = 1 + 5 * (1 - E.out(P(lt, 0.1, 1.0)));
  REG.pink = [(r() - 0.5) * 6 * settle, (r() - 0.5) * 5 * settle];
  REG.yellow = [(r() - 0.5) * 7, (r() - 0.5) * 6];
}
// draw fn() as a second ink pass: multiply blend plus that ink's registration offset
function inkPass(name, fn) {
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.translate(REG[name][0], REG[name][1]); fn(); ctx.restore();
}
const pink = fn => inkPass('pink', fn), yellow = fn => inkPass('yellow', fn);

// halftone dots clipped to a path; size(x, y) returns 0..1 dot radius factor
function halftone(pathFn, col, gap = 10, size = () => 1, ang = 0.26) {
  ctx.save(); ctx.beginPath(); pathFn(); ctx.clip(); ctx.fillStyle = col;
  const c = Math.cos(ang), s = Math.sin(ang);
  ctx.beginPath();
  for (let gy = -H; gy < H * 2; gy += gap) for (let gx = -W * 0.2; gx < W * 1.2; gx += gap) {
    const x = W / 2 + (gx - W / 2) * c - (gy - H / 2) * s, y = H / 2 + (gx - W / 2) * s + (gy - H / 2) * c;
    if (x < -20 || x > W + 20 || y < -20 || y > H + 20) continue;
    const rr = clamp(size(x, y)) * gap * 0.62; if (rr < 0.4) continue;
    ctx.moveTo(x + rr, y); ctx.arc(x, y, rr, 0, 7);
  }
  ctx.fill(); ctx.restore();
}
// a highlighter swipe behind a word, in yellow ink
function hilite(x, y, w, h, u) {
  if (u <= 0) return;
  yellow(() => { const r = rng(Math.round(x)); ctx.fillStyle = C.yellow; ctx.beginPath(); ctx.moveTo(x, y + r() * 4); ctx.lineTo(x + w * u, y + r() * 4); ctx.lineTo(x + w * u - 6, y + h); ctx.lineTo(x + 4, y + h - r() * 4); ctx.fill(); });
}

function background(i, lt) {
  SCENE_I = i; setReg(i, lt);
  ctx.fillStyle = C.bg; ctx.fillRect(0, 0, W, H);
  tile(FIBRE, i, 1);
}
function overlay(i, lt) {
  tile(GRAIN, i * 3 + 1, 1, 'multiply');
  // ink starvation: faint pale bands where the drum ran dry
  const r = rng(i * 7 + 2);
  for (let k = 0; k < 3; k++) { ctx.fillStyle = 'rgba(243,238,227,0.16)'; ctx.fillRect(0, r() * H, W, 8 + r() * 30); }
  if (i > 0) {
    tx(ISSUE, 90, 82, { fam: TEXT, size: 19, w: 600, tr: 4, c: C.ink2, noCheck: true });
    tx('Nº 0' + i, W - 90, 82, { fam: MONO, size: 22, w: 700, c: C.ink2, al: 'right', noCheck: true });
    line(90, 100, W - 90, 100, C.ink3, 1.5);
  }
}
