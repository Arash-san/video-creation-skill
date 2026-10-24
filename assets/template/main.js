// main.js: scene router, transitions and boot. Usually you only change STYLE.transition (in style.js)
// or add your own transition to TRANSITIONS. Scenes live in scenes.js as SC[id] = (lt, cue) => { ... }.
'use strict';
const NS = TL.scenes.length;
const TR = STYLE.transitionDur ?? 1.2;

// cue helpers for the scene being drawn: cue.t(k) start of narration line k, cue.e(k) its end, cue.d scene length
function cueFns(s) { return { t: k => s.lines[Math.min(k, s.lines.length - 1)].t, e: k => { const l = s.lines[Math.min(k, s.lines.length - 1)]; return l.t + l.d; }, d: s.dur, n: s.lines.length }; }

function drawScene(i, lt) {
  const s = TL.scenes[i];
  ctx.save();
  background(i, lt);
  if (!SC[s.id]) { tx('missing scene: ' + s.id, W / 2, H / 2, { size: 48, al: 'center', c: '#f00' }); console.error('missing scene ' + s.id); }
  else SC[s.id](lt, cueFns(s));
  if (typeof overlay === 'function') overlay(i, lt);
  ctx.restore();
}

// Each transition gets (prev, next, u, i): prev() and next() draw the outgoing/incoming scene, u goes 0 -> 1.
const TRANSITIONS = {
  cut(prev, next) { next(); },
  fade(prev, next, u) { next(); ctx.save(); ctx.globalAlpha = 1 - E.io(u); prev(); ctx.restore(); },
  iris(prev, next, u) {   // the next scene opens from a circle in the middle
    next();
    const R = Math.max(0.01, E.io(u) * Math.hypot(W, H) / 2 * 1.05);
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, H); ctx.arc(W / 2, H / 2, R, 0, Math.PI * 2, true); ctx.clip('evenodd'); prev(); ctx.restore();
    ctx.save(); ctx.globalAlpha = 1 - E.in(u); ctx.strokeStyle = C.ink; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(W / 2, H / 2, R, 0, 7); ctx.stroke(); ctx.restore();
  },
  wipe(prev, next, u) {   // a slanted edge sweeps left to right
    next();
    const x = lerp(-300, W + 300, E.io(u)), k = 240;
    ctx.save(); ctx.beginPath(); ctx.moveTo(x + k, 0); ctx.lineTo(W, 0); ctx.lineTo(W, H); ctx.lineTo(x - k, H); ctx.closePath(); ctx.clip(); prev(); ctx.restore();
    line(x + k, 0, x - k, H, C.ink, 5);
  },
  sheet(prev, next, u) {   // the next sheet slides in over the old one with a contact shadow
    prev();
    const x = (1 - E.out5(u)) * W;
    ctx.save(); ctx.translate(x, 0); ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowBlur = 40; ctx.shadowOffsetX = -12;
    ctx.fillStyle = C.bg; ctx.fillRect(0, 0, W, H); ctx.shadowColor = 'transparent';
    ctx.beginPath(); ctx.rect(0, 0, W, H); ctx.clip(); next(); ctx.restore();
  },
  zoom(prev, next, u) {   // dive through the centre of the old scene into the new one
    const v = E.io(u);
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(lerp(0.92, 1, v), lerp(0.92, 1, v)); ctx.translate(-W / 2, -H / 2); next(); ctx.restore();
    ctx.save(); ctx.globalAlpha = 1 - v; ctx.translate(W / 2, H / 2); ctx.scale(1 + v * 1.6, 1 + v * 1.6); ctx.translate(-W / 2, -H / 2); prev(); ctx.restore();
  },
};

function sceneAt(T) { let i = 0; while (i + 1 < NS && T >= TL.scenes[i + 1].start) i++; return i; }

window.renderFrame = function (T) {
  window.__boxes = [];
  const i = sceneAt(T), s = TL.scenes[i], lt = T - s.start;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  window.__inTransition = i > 0 && lt < TR;
  if (window.__inTransition) {
    const tr = typeof STYLE.transition === 'function' ? STYLE.transition : (TRANSITIONS[STYLE.transition] || TRANSITIONS.fade);
    tr(() => drawScene(i - 1, TL.scenes[i - 1].dur + lt), () => drawScene(i, lt), lt / TR, i);
  } else drawScene(i, lt);
};
window.grab = function (fmt) { return document.getElementById('cv').toDataURL(fmt || 'image/png'); };
window.boot = async function () {
  const cv = document.getElementById('cv'); cv.width = W; cv.height = H; ctx = cv.getContext('2d');
  const loads = [];
  for (const fam of new Set([DISPLAY, TEXT, MONO])) for (const w of [300, 400, 500, 600, 700, 800]) { loads.push(F(40, w, fam)); loads.push(F(40, w, fam, true)); }
  await Promise.all(loads.map(f => document.fonts.load(f).catch(() => null)));
  for (const fam of new Set([DISPLAY, TEXT, MONO])) if (!document.fonts.check(F(40, 400, fam))) console.error('font not loaded: ' + fam);
  await loadArt(STYLE.art || []);
  if (typeof prep === 'function') await prep();   // build cached textures, paths, layouts here
  window.READY = true;
};
