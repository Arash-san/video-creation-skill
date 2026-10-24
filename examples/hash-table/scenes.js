// scenes.js (demo): six scenes, every reveal tied to the sentence that explains it.
'use strict';
const SC = {};
const HEAD = { fam: DISPLAY, size: 72, w: 700, c: C.ink };

// ---------------------------------------------------------------- shared pieces
// a row of n bucket cups between x0 and x1; returns geometry so items can be placed in buckets
function bucketGeom(n, x0, x1, gap) { const bw = (x1 - x0 - gap * (n - 1)) / n; return { bw, cx: k => x0 + k * (bw + gap) + bw / 2 }; }
function buckets(n, x0, x1, y0, y1, u = 1, o = {}) {
  const gap = n > 40 ? 2 : n > 12 ? 8 : 12, g = bucketGeom(n, x0, x1, gap);
  for (let k = 0; k < n; k++) {
    const x = g.cx(k) - g.bw / 2, uk = clamp(u * 1.6 - k / n * 0.6);
    if (uk <= 0) continue;
    if (n > 40) { line(g.cx(k), y1, g.cx(k), lerp(y1, y0, E.out(uk)), C.ink3, Math.max(1, g.bw * 0.6)); continue; }
    poly(jitter([[x, y0], [x, y1], [x + g.bw, y1], [x + g.bw, y0]], 1.5, k + 3), E.out(uk), C.ink, 3);
    if (n <= 16 && !o.noLabels) tx(String(k), g.cx(k), y1 + 42, { fam: MONO, size: n > 8 ? 22 : 28, w: 700, c: C.ink2, al: 'center', a: uk });
  }
  return g;
}
// an item tile sitting in a bucket (bottom at y), in pink ink with a blue label
function item(s, cx, y, w, a = 1, o = {}) {
  if (a <= 0) return;
  const h = o.h || 56;
  pink(() => halftone(() => ctx.rect(cx - w / 2, y - h, w, h), C.pink, 7, () => a));
  rect(cx - w / 2, y - h, w, h, { stroke: C.ink, lw: 2.5, a });
  tx(s, cx, y - h / 2 + 8, { fam: MONO, size: o.size || 24, w: 700, c: C.ink, al: 'center', a });
}
function keyBox(s, x, y, a, label = 'KEY') {
  if (a <= 0) return;
  tx(label, x, y - 82, { fam: TEXT, size: 20, w: 700, tr: 5, c: C.pink, a });
  rectDraw(x, y - 66, 240, 120, a, C.ink, 3);
  tx(s, x + 120, y + 14, { fam: MONO, size: 60, w: 700, c: C.ink, al: 'center', a });
}

// ---------------------------------------------------------------- 1. title
SC.title = (lt, cue) => {
  const sx = 1390, sy = 470, R = 320, u = E.out(P(lt, 0.2, 1.8));
  pink(() => halftone(() => ctx.arc(sx, sy, R, 0, 7), C.pink, 13, (x, y) => u * (1.08 - Math.hypot(x - sx, y - sy) / R * 0.8)));
  const keys = ['cat', 'dog', 'ivy', 'kai', 'bo', 'fay', 'gus', 'jo'];
  keys.forEach((k, j) => {
    const a = j / keys.length * Math.PI * 2 + lt * 0.06, r = R + 52;
    tx(k, sx + Math.cos(a) * r, sy + Math.sin(a) * r + 10, { fam: MONO, size: 26, w: 700, c: C.ink, al: 'center', a: E.out(P(lt, 1.2 + j * 0.12, 0.6)) });
  });
  tx('A TWO-INK EXPLAINER', 170, 300, { fam: TEXT, size: 24, w: 700, tr: 7, c: C.ink, a: E.out(P(lt, 0.3, 0.7)) });
  rise('Find it in', 166, 460, { fam: DISPLAY, size: 150, w: 800, c: C.ink }, lt, 0.5, 0.08, 0.9);
  hilite(160, 520, tw('one step.', { fam: DISPLAY, size: 150, w: 800 }) + 16, 110, E.io(P(lt, cue.t(0) + 6.6, 0.7)));
  rise('one step.', 166, 620, { fam: DISPLAY, size: 150, w: 800, c: C.ink }, lt, 0.9, 0.08, 0.9);
  pink(() => rise('one step.', 172, 626, { fam: DISPLAY, size: 150, w: 800, c: C.pink, a: 0.85, noCheck: true }, lt, 1.4, 0.08, 0.9));
  tx('keys  ·  hash functions  ·  buckets  ·  collisions', 170, 740, { fam: TEXT, size: 30, w: 500, c: C.ink2, a: E.out(P(lt, cue.t(0) + 2.5, 0.8)) });
};

// ---------------------------------------------------------------- 2. linear scan
const NAMES = ['ana', 'bo', 'cy', 'dee', 'eli', 'fay', 'gus', 'hal', 'ivy', 'jo', 'kai', 'cat'];
SC.scan = (lt, cue) => {
  rise('Searching a list', 160, 230, HEAD, lt, 0.2);
  pink(() => tx('one item at a time', 164, 290, { fam: TEXT, size: 32, w: 600, c: C.pink, a: E.out(P(lt, 0.9, 0.6)) }));
  const t0 = cue.t(0) + 0.3, t1 = cue.e(0) + 0.9, pos = clamp((lt - t0) / (t1 - t0)) * 11;
  const fade = 1 - E.io(P(lt, cue.t(1) - 0.2, 0.9));
  if (fade > 0) {
    ctx.save(); ctx.globalAlpha = fade;
    NAMES.forEach((nm, k) => {
      const x = 160 + k * 136, y = 400, a = E.out(P(lt, 0.4 + k * 0.05, 0.5));
      if (k === 11 && pos >= 10.95) pink(() => halftone(() => ctx.rect(x, y, 120, 120), C.pink, 8));
      rectDraw(x, y, 120, 120, a, C.ink, 3);
      tx(nm, x + 60, y + 72, { fam: MONO, size: 34, w: 700, c: C.ink, al: 'center', a });
      if (k < 11 && pos > k + 0.5) poly([[x + 14, y + 106], [x + 106, y + 14]], E.out(clamp((pos - k - 0.5) * 3)), C.ink2, 3);
    });
    const px = 160 + pos * 136 + 60;
    pink(() => { ctx.fillStyle = C.pink; ctx.beginPath(); ctx.moveTo(px, 384); ctx.lineTo(px - 16, 356); ctx.lineTo(px + 16, 356); ctx.fill(); });
    if (lt > t0) tx('checks: ' + Math.min(12, Math.floor(pos) + 1), 160, 640, { fam: MONO, size: 40, w: 700, c: C.ink });
    if (pos >= 10.95) pink(() => tx('found it, on the last try', 1792, 640, { fam: TEXT, size: 30, w: 600, c: C.pink, al: 'right', a: E.out(P(lt, t1, 0.5)) }));
    ctx.restore();
  }
  // a million names: the row becomes a dense strip that the pointer must sweep end to end
  const v = E.out(P(lt, cue.t(1), 1.2));
  if (v > 0) {
    for (let k = 0; k < 330; k++) { const x = 160 + k * 5; line(x, 470, x, lerp(470, 400 + (k % 5 === 0 ? -14 : 0), v), C.ink3, 2); }
    const sweep = P(lt, cue.t(1) + 0.8, cue.e(1) - cue.t(1) - 0.4), hx = 160 + sweep * 1645;
    pink(() => { rect(160, 392, hx - 160, 86, { fill: C.pinkS }); line(hx, 380, hx, 490, C.pink, 5); });
    const n = 12 + (1e6 - 12) * E.in(sweep);
    tx(fmtInt(n), W / 2, 700, { fam: MONO, size: 120, w: 700, c: C.ink, al: 'center', a: v });
    tx('checks for one unlucky search', W / 2, 780, { fam: TEXT, size: 32, w: 500, c: C.ink2, al: 'center', a: E.out(P(lt, cue.t(1) + 1.6, 0.6)) });
  }
};

// ---------------------------------------------------------------- 3. hashing a key into a bucket
const BX0 = 1150, BX1 = 1790, BY0 = 360, BY1 = 600;
SC.hash = (lt, cue) => {
  rise('Hashing a key', 160, 230, HEAD, lt, 0.2);
  const ka = E.out(P(lt, 0.6, 0.6));
  keyBox('cat', 150, 480, ka);
  // the hash machine: a hopper with a halftone body that shakes while it works
  const shake = lt > cue.t(0) + 4.0 && lt < cue.t(0) + 5.0 ? Math.sin(lt * 70) * 3 : 0;
  const ma = E.out(P(lt, 1.0, 0.8));
  ctx.save(); ctx.translate(shake, 0); ctx.globalAlpha = ma;
  const hop = () => { ctx.moveTo(600, 330); ctx.lineTo(1000, 330); ctx.lineTo(870, 560); ctx.lineTo(870, 610); ctx.lineTo(730, 610); ctx.lineTo(730, 560); ctx.closePath(); };
  pink(() => halftone(hop, C.pink, 11, (x, y) => 0.25 + (y - 330) / 280 * 0.8));
  ctx.beginPath(); hop(); ctx.strokeStyle = C.ink; ctx.lineWidth = 3.5; ctx.lineJoin = 'round'; ctx.stroke();
  tx('hash( )', 800, 440, { fam: DISPLAY, size: 52, w: 800, c: C.ink, al: 'center' });
  ctx.restore();
  // letters fly from the key into the hopper
  ['c', 'a', 't'].forEach((ch, j) => {
    const u = P(lt, cue.t(0) + 2.6 + j * 0.25, 0.9);
    if (u <= 0 || u >= 1) return;
    const sx = 230 + j * 38, pts = qpts(sx, 470, 520, 160, 800, 340), p = pts[Math.round(E.io(u) * 40)];
    tx(ch, p[0], p[1], { fam: MONO, size: 60, w: 700, c: C.ink, al: 'center', a: 1 - E.in(u), noCheck: true });
  });
  // a number comes out, then the remainder picks a bucket
  const numStr = '3,204,571';
  const nu = P(lt, cue.t(0) + 5.2, 1.0);
  if (nu > 0) typed(numStr, 800 - tw(numStr, { fam: MONO, size: 52, w: 700 }) / 2, 690, { fam: MONO, size: 52, w: 700, c: C.ink }, nu);
  const mu = E.out(P(lt, cue.t(1) + 0.1, 0.6));
  const modStr = '% 8 = 3', mw = tw(modStr, { fam: MONO, size: 44, w: 700 });
  hilite(800 - mw / 2 - 10, 734, mw + 20, 52, E.io(P(lt, cue.t(1) + 0.7, 0.5)));
  tx(modStr, 800, 772, { fam: MONO, size: 44, w: 700, c: C.ink, al: 'center', a: mu });
  const g = buckets(8, BX0, BX1, BY0, BY1, P(lt, 0.8, 1.4));
  carrow(980, 760, 1380, 800, g.cx(3), 680, P(lt, cue.t(1) + 0.9, 0.8), C.pink, 4, { head: 16 });
  const drop = E.back(P(lt, cue.t(1) + 1.6, 0.7));
  if (drop > 0) item('cat', g.cx(3), lerp(250, BY1 - 4, drop), g.bw - 10);
  tx('cat → "Felis catus"', g.cx(3), 320, { fam: MONO, size: 26, w: 700, c: C.ink, al: 'center', a: E.out(P(lt, cue.t(1) + 2.3, 0.6)) });
};

// ---------------------------------------------------------------- 4. lookup is one jump
SC.lookup = (lt, cue) => {
  rise('Looking it up', 160, 230, HEAD, lt, 0.2);
  // the table grows from 8 buckets to many; the jump still lands in one step
  const gu = P(lt, cue.t(1) + 0.3, 3.2), levels = [8, 16, 32, 64, 128, 256, 512], n = levels[Math.min(6, Math.floor(gu * 7))];
  const target = Math.round(3 / 8 * n);
  const g = buckets(n, BX0, BX1, BY0, BY1, 1, { noLabels: n > 8 });
  const tx3 = g.cx(target);
  if (n <= 16) item('cat', tx3, BY1 - 4, g.bw - 10);
  else pink(() => rect(tx3 - Math.max(3, g.bw) / 2, BY1 - 60, Math.max(4, g.bw), 60, { fill: C.pink }));
  tx('find("cat")', 150, 470, { fam: MONO, size: 50, w: 700, c: C.ink, a: E.out(P(lt, 0.5, 0.6)) });
  const hs = 'hash → 3,204,571 % 8 = 3';
  pink(() => typed(hs, 150, 530, { fam: MONO, size: 28, w: 700, c: C.pink }, P(lt, cue.t(0) + 2.2, 1.4)));
  const jumps = [cue.t(0) + 4.3, cue.t(1) + 1.2, cue.t(1) + 3.2];
  jumps.forEach((tj, j) => {
    const u = P(lt, tj, 0.7), fade = 1 - P(lt, tj + 1.3, 0.6);
    if (u <= 0 || fade <= 0) return;
    ctx.save(); ctx.globalAlpha = fade;
    carrow(520, 450, (520 + tx3) / 2, 130, tx3, BY0 - 20, E.io(u), C.pink, 5, { head: 18 });
    const b = P(lt, tj + 0.7, 0.8);
    if (b > 0 && b < 1) pink(() => halftone(() => ctx.arc(tx3, BY1 - 40, 40 + b * 110, 0, 7), C.pink, 9, () => (1 - b) * 0.9));
    ctx.restore();
  });
  const sa = E.out(P(lt, cue.t(0) + 5.0, 0.6));
  hilite(144, 726, tw('steps: 1', { fam: MONO, size: 48, w: 700 }) + 14, 58, E.io(P(lt, cue.t(1) + 0.4, 0.5)));
  tx('steps: 1', 150, 770, { fam: MONO, size: 48, w: 700, c: C.ink, a: sa });
  const nb = n >= 512 ? 8 * Math.pow(2, 17 * clamp((lt - cue.t(1) - 3.5) / 2.0)) : n;
  tx('buckets: ' + fmtInt(nb), 150, 830, { fam: MONO, size: 30, w: 700, c: C.ink2, a: E.out(P(lt, cue.t(1), 0.6)) });
};

// ---------------------------------------------------------------- 5. collisions, chaining, resizing
const CX0 = 900, CX1 = 1790;
SC.collide = (lt, cue) => {
  rise('When two keys collide', 160, 230, HEAD, lt, 0.2);
  keyBox('dog', 150, 480, E.out(P(lt, 0.5, 0.6)));
  pink(() => typed('hash("dog") % 8 = 3', 150, 600, { fam: MONO, size: 30, w: 700, c: C.pink }, P(lt, cue.t(0) + 0.4, 1.2)));
  // grow 8 -> 16 buckets late in the second line; items keep their buckets or move
  const gr = E.io(P(lt, cue.t(1) + 3.4, 1.2));
  const g8 = bucketGeom(8, CX0, CX1, 12), g16 = bucketGeom(16, CX0, CX1, 8);
  if (gr < 1) { ctx.save(); ctx.globalAlpha = 1 - gr; buckets(8, CX0, CX1, BY0, BY1); ctx.restore(); }
  if (gr > 0) { ctx.save(); ctx.globalAlpha = gr; buckets(16, CX0, CX1, BY0, BY1); ctx.restore(); }
  const bw = lerp(g8.bw, g16.bw, gr) - 8, fs = lerp(24, 18, gr);
  const catX = lerp(g8.cx(3), g16.cx(3), gr);
  item('cat', catX, BY1 - 4, bw, 1, { size: fs });
  // dog arrives, bounces off cat (collision), then settles on top as a two-item list
  const arrow0 = P(lt, cue.t(0) + 1.4, 0.7);
  carrow(400, 470, 700, 260, g8.cx(3), BY0 - 30, arrow0, C.ink, 3, { a: 1 - P(lt, cue.t(0) + 2.9, 0.4) });
  const fall = P(lt, cue.t(0) + 2.2, 0.55), bounce = P(lt, cue.t(0) + 2.75, 0.8), link = P(lt, cue.t(1) + 0.6, 0.6);
  const top = BY1 - 70;   // resting on top of cat: the bucket now holds a two-item list
  let dy = lerp(200, top, E.in(fall));
  if (bounce > 0) dy = top - 130 * Math.sin(Math.PI * bounce) * (1 - bounce * 0.4);
  const dogX = lerp(g8.cx(3), g16.cx(11), gr), dogY = lerp(dy, BY1 - 4, gr);
  if (fall > 0) item('dog', dogX, dogY, bw, 1, { size: fs });
  if (link > 0 && gr < 1) { ctx.save(); ctx.globalAlpha = 1 - gr; arrow(g8.cx(3) + bw / 2 + 14, top - 28, g8.cx(3) + bw / 2 + 14, BY1 - 32, E.out(link), C.pink, 3, { head: 10 }); ctx.restore(); }
  // the stamp
  const st = P(lt, cue.t(0) + 3.4, 0.35), sa = st * (1 - P(lt, cue.t(1) + 0.2, 0.5));
  if (sa > 0) {
    ctx.save(); ctx.translate(g8.cx(3), 270); ctx.rotate(-0.1); const s = lerp(1.6, 1, E.out(st)); ctx.scale(s, s);
    pink(() => { tx('collision!', 0, 0, { fam: DISPLAY, size: 84, w: 800, c: C.pink, al: 'center', a: sa }); });
    ctx.restore();
  }
  tx('a short list per bucket', 150, 700, { fam: TEXT, size: 34, w: 600, c: C.ink, a: E.out(P(lt, cue.t(1) + 0.9, 0.6)) * (1 - gr * 0.6) });
  const lab = E.out(P(lt, cue.t(1) + 3.6, 0.6));
  hilite(144, 744, tw('8 → 16 buckets', { fam: MONO, size: 40, w: 700 }) + 14, 52, E.io(P(lt, cue.t(1) + 4.3, 0.5)));
  tx('8 → 16 buckets', 150, 784, { fam: MONO, size: 40, w: 700, c: C.ink, a: lab });
};

// ---------------------------------------------------------------- 6. outro: the trade
SC.outro = (lt, cue) => {
  const tilt = 0.11 * E.back(P(lt, cue.t(0) + 1.4, 1.0)), px = W / 2, py = 400;
  const ba = E.out(P(lt, 0.3, 0.7));
  // fulcrum
  ctx.save(); ctx.globalAlpha = ba;
  pink(() => halftone(() => { ctx.moveTo(px, py + 6); ctx.lineTo(px - 70, py + 110); ctx.lineTo(px + 70, py + 110); ctx.closePath(); }, C.pink, 8));
  ctx.beginPath(); ctx.moveTo(px, py + 6); ctx.lineTo(px - 70, py + 110); ctx.lineTo(px + 70, py + 110); ctx.closePath(); ctx.strokeStyle = C.ink; ctx.lineWidth = 3; ctx.stroke();
  // beam with a small memory block and a big speed block
  ctx.translate(px, py); ctx.rotate(tilt);
  line(-470, 0, 470, 0, C.ink, 6);
  pink(() => halftone(() => ctx.rect(-420, -80, 80, 80), C.pink, 7));
  rect(-420, -80, 80, 80, { stroke: C.ink, lw: 3 });
  rect(250, -170, 170, 170, { fill: C.ink });
  tx('a little memory', -380, -110, { fam: TEXT, size: 30, w: 600, c: C.ink, al: 'center' });
  tx('a lot of speed', 335, -200, { fam: TEXT, size: 30, w: 600, c: C.ink, al: 'center' });
  ctx.restore();
  // the takeaway
  const o = { fam: DISPLAY, size: 104, w: 800, c: C.ink, al: 'center' }, s = "compute, don't search.";
  const x0 = W / 2 - tw(s, o) / 2, cw = tw('compute,', o), sx = x0 + tw("compute, don't ", o), sw = tw('search', o);
  hilite(x0 - 8, 640, cw + 16, 86, E.io(P(lt, cue.t(0) + 4.6, 0.5)));
  rise(s, W / 2, 720, o, lt, cue.t(0) + 3.6, 0.09, 0.8);
  pink(() => poly(jitter([[sx - 6, 690], [sx + sw * 0.5, 684], [sx + sw + 8, 688]], 3, 9), E.out(P(lt, cue.t(0) + 6.0, 0.6)), C.pink, 10));
  pink(() => tx('fin.', 1780, 840, { fam: DISPLAY, size: 40, w: 800, c: C.pink, al: 'right', a: E.out(P(lt, cue.e(0) + 0.6, 0.6)) }));
};
