// core.js: style-agnostic drawing and animation helpers for canvas videos.
// Everything is a pure function of time: renderFrame(t) must draw the same frame every time it is called
// with the same t, so frames can be rendered in any order and in parallel. Never keep animation state
// between frames; derive it from `lt` (scene-local seconds) and the narration cues.
'use strict';
const W = (typeof TL !== 'undefined' && TL.width) || 1920, H = (typeof TL !== 'undefined' && TL.height) || 1080;
const SAFE_BOTTOM = (typeof TL !== 'undefined' && TL.subtitle_top) || 900;   // keep content above the subtitle band
const DISPLAY = STYLE.fonts.display, TEXT = STYLE.fonts.text, MONO = STYLE.fonts.mono;
let ctx = null;

// ---------------------------------------------------------------- time and easing
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const P = (t, a, d) => clamp((t - a) / d);              // progress 0..1 of an animation that starts at a and lasts d
const lerp = (a, b, u) => a + (b - a) * u;
const smooth = x => x * x * (3 - 2 * x);
const E = {
  out: x => 1 - Math.pow(1 - x, 3),
  out5: x => 1 - Math.pow(1 - x, 5),
  io: x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2,
  in: x => x * x * x,
  back: x => { const c1 = 1.6, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); },
  elastic: x => x === 0 || x === 1 ? x : Math.pow(2, -10 * x) * Math.sin((x * 10 - 0.75) * (2 * Math.PI / 3)) + 1,
};
// in-and-out envelope: rises over `fade` after a, holds, falls over `fade` before b
const span = (t, a, b, fade = 0.5) => Math.min(E.out(P(t, a, fade)), 1 - E.in(P(t, b - fade, fade)));
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function noise1(x, seed = 1) { const i = Math.floor(x), f = x - i, h = n => { const r = rng(n * 7919 + seed); return r(); }; return lerp(h(i), h(i + 1), smooth(f)); }
function mkCanvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

// ---------------------------------------------------------------- text
function F(size, w = 400, fam = TEXT, it = false) { return `${it ? 'italic ' : ''}${w} ${size}px "${fam}"`; }
function setFont(o) { ctx.font = F(o.size || 32, o.w || 400, o.fam || TEXT, o.it); ctx.letterSpacing = (o.tr || 0) + 'px'; }
function tw(s, o = {}) { ctx.save(); setFont(o); const w = ctx.measureText(s).width; ctx.restore(); return w; }
function _logBox(s, x, y, o) {   // used by `render.py check` to find overlapping or misplaced text
  if (!window.LAYOUT || o.noCheck) return;
  const m = ctx.measureText(s), T = ctx.getTransform(), a = ctx.globalAlpha;
  const xs = [x - m.actualBoundingBoxLeft, x + m.actualBoundingBoxRight], ys = [y - m.actualBoundingBoxAscent, y + m.actualBoundingBoxDescent];
  const pts = [[xs[0], ys[0]], [xs[1], ys[0]], [xs[0], ys[1]], [xs[1], ys[1]]].map(([px, py]) => [T.a * px + T.c * py + T.e, T.b * px + T.d * py + T.f]);
  (window.__boxes = window.__boxes || []).push({ s, a, x0: Math.min(...pts.map(p => p[0])), x1: Math.max(...pts.map(p => p[0])), y0: Math.min(...pts.map(p => p[1])), y1: Math.max(...pts.map(p => p[1])) });
}
// tx(s, x, y, {size, w, fam, it, c, a, al, bl, tr, glow, gb, noCheck})
function tx(s, x, y, o = {}) {
  if (!s) return;
  ctx.save(); setFont(o);
  ctx.fillStyle = o.c || C.ink; ctx.globalAlpha *= (o.a ?? 1);
  ctx.textAlign = o.al || 'left'; ctx.textBaseline = o.bl || 'alphabetic';
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.gb || 18; }
  if (o.stroke) { ctx.strokeStyle = o.stroke; ctx.lineWidth = o.slw || 3; ctx.lineJoin = 'round'; ctx.strokeText(s, x, y); }
  ctx.fillText(s, x, y);
  _logBox(s, x, y, o);
  ctx.restore();
}
// words rise one after another; *asterisks* mark an emphasis span drawn italic in o.itc
function rise(s, x, y, o, lt, t0, stag = 0.06, dur = 0.6) {
  const items = []; let inIt = false;
  for (const p of s.split(' ')) {
    if (p.startsWith('*')) inIt = true;
    items.push({ w: p.replace(/\*/g, ''), it: inIt });
    if (/\*[.,:;!?]?$/.test(p)) inIt = false;
  }
  const sp = tw(' ', o), wOf = p => tw(p.w, { ...o, it: p.it || o.it });
  let total = 0; items.forEach((p, i) => total += wOf(p) + (i ? sp : 0));
  let cx = o.al === 'center' ? x - total / 2 : o.al === 'right' ? x - total : x;
  items.forEach((p, i) => {
    const u = E.out(P(lt, t0 + i * stag, dur));
    if (u > 0) tx(p.w, cx, y + (1 - u) * (o.size || 32) * 0.55, { ...o, al: 'left', it: p.it || o.it, c: p.it && o.itc ? o.itc : o.c, a: (o.a ?? 1) * u });
    cx += wOf(p) + sp;
  });
  return total;
}
function wrap(s, maxw, o) {
  const words = s.split(' '), lines = []; let cur = '';
  for (const w of words) { const t = cur ? cur + ' ' + w : w; if (tw(t, o) > maxw && cur) { lines.push(cur); cur = w; } else cur = t; }
  if (cur) lines.push(cur); return lines;
}
function para(s, x, y, maxw, lh, o, lt, t0, stag = 0.12) {
  const ls = wrap(s, maxw, o);
  ls.forEach((l, i) => rise(l, x, y + i * lh, o, lt, t0 + i * stag, 0.03, 0.55));
  return ls.length;
}
function typed(s, x, y, o, u) {   // typewriter with a block cursor
  const n = Math.floor(s.length * clamp(u));
  tx(s.slice(0, n), x, y, { ...o, noCheck: u < 1 || o.noCheck });
  if (u > 0 && u < 1) { const w = tw(s.slice(0, n), o), sz = o.size || 32; ctx.save(); ctx.fillStyle = o.c || C.ink; ctx.globalAlpha *= 0.7; ctx.fillRect(x + w + 4, y - sz * 0.75, sz * 0.09, sz * 0.9); ctx.restore(); }
}
function num(s, x, y, o) {   // fixed-width digits so counters never jitter
  const cw = (o.size || 40) * (o.cell || 0.6); let wsum = 0;
  for (const ch of s) wsum += /[0-9]/.test(ch) ? cw : tw(ch, o);
  let cx = o.al === 'right' ? x - wsum : o.al === 'center' ? x - wsum / 2 : x;
  for (const ch of s) {
    if (/[0-9]/.test(ch)) { tx(ch, cx + cw / 2, y, { ...o, al: 'center', noCheck: true }); cx += cw; }
    else { tx(ch, cx, y, { ...o, al: 'left', noCheck: true }); cx += tw(ch, o); }
  }
}
const fmtInt = v => Math.round(v).toLocaleString('en-US');

// ---------------------------------------------------------------- strokes and shapes
function line(x1, y1, x2, y2, col = C.ink, lw = 2, dash = null, a = 1) {
  ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.globalAlpha *= a; ctx.lineCap = 'round'; if (dash) ctx.setLineDash(dash);
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.restore();
}
// draw the first u (0..1) of a polyline's length; returns the pen position (handy for a glowing head)
function poly(pts, u, col = C.ink, lw = 2.5, o = {}) {
  if (u <= 0 || pts.length < 2) return null;
  const seg = []; let L = 0;
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); L += d; }
  const rem = L * clamp(u), u0 = o.from ? L * clamp(o.from) : 0;
  ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = o.cap || 'round'; ctx.lineJoin = 'round';
  if (o.dash) { ctx.setLineDash(o.dash); ctx.lineDashOffset = o.off || 0; }
  if (o.a != null) ctx.globalAlpha *= o.a;
  if (o.comp) ctx.globalCompositeOperation = o.comp;
  ctx.beginPath();
  let acc = 0, started = false, hx = pts[0][0], hy = pts[0][1];
  for (let i = 1; i < pts.length; i++) {
    const a0 = acc, a1 = acc + seg[i - 1], s0 = Math.max(a0, u0), s1 = Math.min(a1, rem);
    if (s1 > s0) {
      const f0 = (s0 - a0) / seg[i - 1], f1 = (s1 - a0) / seg[i - 1];
      const x0 = lerp(pts[i - 1][0], pts[i][0], f0), y0 = lerp(pts[i - 1][1], pts[i][1], f0);
      hx = lerp(pts[i - 1][0], pts[i][0], f1); hy = lerp(pts[i - 1][1], pts[i][1], f1);
      if (!started) { ctx.moveTo(x0, y0); started = true; }
      ctx.lineTo(hx, hy);
    }
    acc = a1;
  }
  ctx.stroke(); ctx.restore();
  return [hx, hy];
}
function qpts(x1, y1, cx, cy, x2, y2, n = 40) { const p = []; for (let i = 0; i <= n; i++) { const t = i / n; p.push([(1 - t) * (1 - t) * x1 + 2 * (1 - t) * t * cx + t * t * x2, (1 - t) * (1 - t) * y1 + 2 * (1 - t) * t * cy + t * t * y2]); } return p; }
function arcPts(cx, cy, r, a0, a1, n = 64) { const p = []; for (let i = 0; i <= n; i++) { const a = lerp(a0, a1, i / n); p.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); } return p; }
function head(x, y, ang, col, s = 13, a = 1) {
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = col; ctx.beginPath();
  ctx.moveTo(x, y); ctx.lineTo(x - s * Math.cos(ang - 0.42), y - s * Math.sin(ang - 0.42)); ctx.lineTo(x - s * Math.cos(ang + 0.42), y - s * Math.sin(ang + 0.42)); ctx.fill(); ctx.restore();
}
function arrow(x1, y1, x2, y2, u, col = C.ink, lw = 2.5, o = {}) {
  if (u <= 0) return;
  const hx = lerp(x1, x2, clamp(u)), hy = lerp(y1, y2, clamp(u));
  line(x1, y1, hx, hy, col, lw, o.dash, o.a ?? 1);
  head(hx, hy, Math.atan2(y2 - y1, x2 - x1), col, o.head || 13, (o.a ?? 1) * clamp(u * 3));
}
function carrow(x1, y1, cx, cy, x2, y2, u, col = C.ink, lw = 2.5, o = {}) {   // curved arrow
  const pts = qpts(x1, y1, cx, cy, x2, y2), h = poly(pts, u, col, lw, o);
  if (!h || u < 0.05) return;
  const k = Math.max(1, Math.floor(pts.length * clamp(u)) - 2), a = pts[k - 1] || pts[0];
  head(h[0], h[1], Math.atan2(h[1] - a[1], h[0] - a[0]), col, o.head || 13, o.a ?? 1);
}
function circle(x, y, r, o = {}) {
  ctx.save(); ctx.globalAlpha *= (o.a ?? 1); ctx.beginPath();
  if (o.u != null && o.u < 1) ctx.arc(x, y, r, -Math.PI / 2, -Math.PI / 2 + 2 * Math.PI * clamp(o.u)); else ctx.arc(x, y, r, 0, 2 * Math.PI);
  if (o.fill) { ctx.fillStyle = o.fill; ctx.fill(); }
  if (o.stroke) { ctx.strokeStyle = o.stroke; ctx.lineWidth = o.lw || 2; if (o.dash) ctx.setLineDash(o.dash); ctx.stroke(); }
  ctx.restore();
}
function rect(x, y, w, h, o = {}) {
  ctx.save(); ctx.globalAlpha *= (o.a ?? 1);
  if (o.comp) ctx.globalCompositeOperation = o.comp;
  if (o.fill) { ctx.fillStyle = o.fill; ctx.fillRect(x, y, w, h); }
  if (o.stroke) { ctx.strokeStyle = o.stroke; ctx.lineWidth = o.lw || 2; if (o.dash) ctx.setLineDash(o.dash); ctx.strokeRect(x, y, w, h); }
  ctx.restore();
}
function rectDraw(x, y, w, h, u, col = C.ink, lw = 2, o = {}) { return poly([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], u, col, lw, o); }
function underline(x1, x2, y, u, col = C.ink, lw = 3, seed = 1) {   // hand-drawn underline
  const r = rng(seed), pts = []; for (let i = 0; i <= 30; i++) { const f = i / 30; pts.push([lerp(x1, x2, f), y + Math.sin(f * 9 + r() * 3) * 1.6 + f * 2]); }
  poly(pts, E.out(u), col, lw);
}
// wobbly hand-drawn version of any polyline (deterministic per seed)
function jitter(pts, amp = 2, seed = 1) { const r = rng(seed); return pts.map(([x, y]) => [x + (r() - 0.5) * amp, y + (r() - 0.5) * amp]); }
function hatch(pathFn, ang = 0.8, gap = 7, col = C.ink, lw = 1, a = 0.4) {   // engraved/hatched fill inside a path
  ctx.save(); ctx.beginPath(); pathFn(); ctx.clip();
  ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.globalAlpha *= a; ctx.beginPath();
  const c = Math.cos(ang), s = Math.sin(ang);
  for (let d = -2400; d < 2400; d += gap) { ctx.moveTo(W / 2 - c * 2400 - s * d, H / 2 - s * 2400 + c * d); ctx.lineTo(W / 2 + c * 2400 - s * d, H / 2 + s * 2400 + c * d); }
  ctx.stroke(); ctx.restore();
}
function glow(x, y, r, col, a = 1, comp = 'lighter') {
  ctx.save(); ctx.globalCompositeOperation = comp; ctx.globalAlpha *= a;
  const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, col); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); ctx.restore();
}

// ---------------------------------------------------------------- camera and images
// withCam({x, y, z, r}) draws fn() as if the camera looks at world point (x, y) with zoom z and rotation r
function withCam(cam, fn) {
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(cam.z || 1, cam.z || 1); if (cam.r) ctx.rotate(cam.r); ctx.translate(-cam.x, -cam.y); fn(); ctx.restore();
}
// camera path through keyframes [[t, {x,y,z}], ...] with eased segments
function camAt(t, keys, ease = E.io) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) {
    const [t0, a] = keys[i - 1], [t1, b] = keys[i], u = ease((t - t0) / (t1 - t0));
    return { x: lerp(a.x, b.x, u), y: lerp(a.y, b.y, u), z: Math.exp(lerp(Math.log(a.z || 1), Math.log(b.z || 1), u)), r: lerp(a.r || 0, b.r || 0, u) };
  }
  return keys[keys.length - 1][1];
}
const ART = {};
function loadArt(names) {
  return Promise.all(names.map(n => new Promise(res => { const im = new Image(); im.crossOrigin = 'anonymous'; im.onload = () => { ART[n] = im; res(); }; im.onerror = () => { console.error('missing art: ' + n); res(); }; im.src = `art/${n}_a.png`; })));
}
function plate(name, x, y, w, a = 1, o = {}) {   // draw a keyed art plate centred at (x, y) by width
  const im = ART[name]; if (!im || a <= 0) return null;
  const h = w * im.height / im.width;
  ctx.save(); ctx.globalAlpha *= a; ctx.imageSmoothingQuality = 'high';
  if (o.clip) { ctx.beginPath(); o.clip(); ctx.clip(); }
  if (o.comp) ctx.globalCompositeOperation = o.comp;
  ctx.drawImage(im, x - w / 2, y - h / 2, w, h); ctx.restore();
  return [w, h];
}
function clipCircle(x, y, r, fn) { ctx.save(); ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.clip(); fn(); ctx.restore(); }

// ---------------------------------------------------------------- procedural textures (cache once in boot/prep)
// grain(seed, rgb, strength): a tileable speckle canvas for paper, film or print noise
function grainTexture(seed = 7, rgb = [0, 0, 0], strength = 26, S = 512) {
  const c = mkCanvas(S, S), g = c.getContext('2d'), r = rng(seed), im = g.createImageData(S, S), d = im.data;
  for (let i = 0; i < S * S; i++) { d[i * 4] = rgb[0]; d[i * 4 + 1] = rgb[1]; d[i * 4 + 2] = rgb[2]; d[i * 4 + 3] = Math.pow(r(), 3) * strength; }
  g.putImageData(im, 0, 0); return c;
}
function tile(tex, seed = 0, a = 1, comp = 'source-over') {   // cover the frame with a texture, shifted per seed so it lives
  const pat = ctx.createPattern(tex, 'repeat');
  pat.setTransform(new DOMMatrix().translate((seed * 377) % tex.width, (seed * 211) % tex.height));
  ctx.save(); ctx.globalAlpha *= a; ctx.globalCompositeOperation = comp; ctx.fillStyle = pat; ctx.fillRect(0, 0, W, H); ctx.restore();
}
function vignette(col = 'rgba(0,0,0,0.35)', inner = 0.45) {
  const g = ctx.createRadialGradient(W / 2, H / 2, H * inner, W / 2, H / 2, H * 1.05);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, col); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
