// scenes.js: one function per scene id in narration.json. SC[id] = (lt, cue) => { ... }
//   lt       seconds since the scene started (transitions also call it past its end)
//   cue.t(k) when narration line k of this scene starts; cue.e(k) when it ends; cue.d scene length
// Tie every reveal to the sentence that explains it: P(lt, cue.t(1), 0.8) is 0 -> 1 as line 1 begins.
'use strict';
const SC = {};

SC.title = (lt, cue) => {
  rise('Your *title* here', W / 2, 470, { fam: DISPLAY, size: 110, c: C.ink, itc: C.a1, al: 'center' }, lt, 0.3, 0.08, 0.9);
  tx('A subtitle that says who this is for', W / 2, 560, { size: 34, c: C.ink2, al: 'center', a: E.out(P(lt, 1.2, 0.8)) });
  underline(W / 2 - 300, W / 2 + 300, 600, P(lt, cue.t(0), 1.2), C.a1, 4);
};
