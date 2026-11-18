/* Bespoke Computer Science Stick-Figure Scenes for Episode 01 (IRCTC Tatkal Concurrency).
 * Built strictly on window.RIG (MIT, Kamran Ahmed / nilbuild/stick-scene) so joints/elbows/feet stay natural.
 */
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, text, seg, breathe, sparks, pulse, lp, bubble, circle } = R;

  SC['tatkal_typing_panic'] = {
    dur: 6,
    width: 225,
    label: 'At 9:59:58 AM a traveler types frantically on a laptop to book an IRCTC Tatkal seat, slams book, and sees WL 180.',
    draw(g, S) {
      const T = S.u * this.dur;
      const w = S.w;
      const keysX = 36, keysY = -55;
      const deskX = -10, deskW = 104;

      // Desk + monitor back props
      ln(g, deskX + 8, -46, deskX + 4, 0, 2.2);
      ln(g, deskX + deskW - 8, -46, deskX + deskW - 4, 0, 2.2);
      rr(g, deskX, -50, deskW, 6, 2);
      inkFill(g, C.wood, 1.5);
      // Laptop base + angled screen
      rr(g, keysX - 24, -55, 48, 5, 1.5);
      inkFill(g, '#e4e6e9', 1.3);
      rr(g, keysX + 16, -98, 42, 44, 3);
      inkFill(g, '#0f172a', 1.6);

      // Screen text reacts to booking attempt
      const clicked = S.on && T > 3.1;
      const wl = S.on && T > 3.7;
      text(g, wl ? 'WL 180' : 'AVL 042', keysX + 37, -78, 8.5, wl ? '#fb7185' : '#34d399');
      text(g, clicked ? 'WAIT...' : '09:59:58', keysX + 37, -65, 7, '#fcd34d');

      // Walk traveler from -92 to -26, type rapidly, slam enter at T=3.0, recoil at T=3.9
      let x = -34;
      let gait = null;
      if (S.on && T < 0.8) {
        const ws = walkSeg(T, 0, 0.8, -76, -34);
        x = ws.x;
        gait = ws;
      } else if (!S.on) {
        x = -34;
      }

      const rest = P({ hF: [12, -56], hB: [-4, -52] });
      const bob = S.on ? Math.sin(T * 26) * 2.5 * (1 - seg(T, 2.7, 3.0)) : Math.sin(S.t * 3.0) * 0.6;
      const typePose = P({
        chest: [4, -89],
        head: [9, -113],
        hF: lp([keysX - 4, keysY + bob], x, 0, 1),
        hB: lp([keysX - 16, keysY - bob], x, 0, 1),
        ef: 0.75,
        eb: 0.85,
      });
      const slamUp = P({
        chest: [2, -91],
        head: [8, -115],
        hF: lp([keysX - 2, -92], x, 0, 1),
        hB: [-4, -54],
      });
      const slamDn = P({
        chest: [6, -88],
        head: [11, -112],
        hF: lp([keysX - 4, keysY], x, 0, 1),
        hB: [-4, -54],
      });
      const shock = P({
        chest: [-4, -90],
        head: [-6, -116],
        hF: [16, -124],
        hB: [-12, -116],
      });

      let pose = rest;
      if (!S.on) {
        const idleChk = pulse(S.t, 5.5, 1.8, 1.3);
        pose = mix(typePose, P({ head: [8, -114], hF: [10, -96], hB: [-4, -54] }), idleChk * 0.65);
      } else {
        const toType = E.soft(seg(T, 0.5, 1.0));
        const toUp = E.soft(seg(T, 2.65, 2.95));
        const toSlam = E.in(seg(T, 2.95, 3.15));
        const toShock = E.back(seg(T, 3.65, 4.15));
        const toRest = E.soft(seg(T, 5.3, 6.0));
        pose = mix(rest, typePose, toType);
        pose = mix(pose, slamUp, toUp);
        pose = mix(pose, slamDn, toSlam);
        pose = mix(pose, shock, toShock);
        pose = mix(pose, rest, toRest);
      }
      pose = breathe(pose, S.t, 0.8);
      if (gait) {
        pose = legs(pose, gait.ph, gait.amp, { arms: false, stride: gait.stride });
      }

      const J = fig(g, pose, x, 0, { sx: 1, ink: '#141414' });

      // Sweat / sparks on key slam
      if (S.on && T >= 3.1 && T < 3.7) {
        sparks(g, keysX - 4, keysY - 4, seg(T, 3.1, 3.7), 6, 18);
      }
      if (S.on && T >= 3.85 && T < 5.5) {
        const fadeOut = 1 - seg(T, 5.1, 5.5);
        g.save();
        g.globalAlpha *= fadeOut;
        bubble(g, x - 34, -142, 'WL 180?!', 1, E.back(seg(T, 3.85, 4.25)), C.red, C.redInk);
        g.restore();
      }
      void J;
      void w;
    },
  };

  SC['tatkal_mutex_race'] = {
    dur: 6,
    width: 265,
    label: 'Two requests race toward a single seat lock lever; the faster thread pulls the mutex lock first while the slower arrives late to WL 180.',
    draw(g, S) {
      const T = S.u * this.dur;
      const locked = S.on && T > 2.2;
      const pullK = S.on ? E.soft(seg(T, 1.85, 2.35)) * (1 - E.soft(seg(T, 5.2, 5.8))) : 0;

      // Center Database Seat Lock Console + Lever (x = 0)
      ln(g, -22, -62, -18, 0, 2.2);
      ln(g, 22, -62, 18, 0, 2.2);
      rr(g, -28, -98, 56, 38, 5);
      inkFill(g, locked ? C.green : C.butterSoft, 1.7);
      text(g, 'B3-42', 0, -83, 9, C.ink);
      text(g, locked ? 'MUTEX LOCKED' : 'OPEN', 0, -68, 7.5, locked ? C.greenInk : C.amber);

      // Lever pivot on right side of console (+28, -76)
      const ang = -0.65 + pullK * 1.35;
      const lx = 28 + Math.sin(ang) * 26;
      const ly = -76 - Math.cos(ang) * 26;
      ln(g, 28, -76, lx, ly, 3.0, C.ink);
      circle(g, lx, ly, 4.5);
      inkFill(g, C.butterHi, 1.4);

      // Fast Fiber Bot starts at +138 -> walks left to +48 -> pulls lever -> celebrates
      let bx = 120, bGait = null;
      if (S.on && T < 1.55) {
        const ws = walkSeg(T, 0, 1.55, 132, 56);
        bx = ws.x;
        bGait = ws;
      } else if (S.on && T >= 1.55 && T < 5.0) {
        bx = 56;
      } else if (S.on && T >= 5.0) {
        const ws = walkSeg(T, 5.0, 5.9, 56, 120);
        bx = ws.x;
        bGait = { ph: -ws.ph, amp: ws.amp, stride: ws.stride };
      }

      const bRest = P({ hF: [10, -56], hB: [-4, -52] });
      const bReach = P({ chest: [3, -89], head: [7, -114], hF: lp([lx, ly], bx, 0, -1), hB: [-4, -52] });
      const bCheer = P({ head: [3, -117], hF: [14, -130], hB: [-10, -126] });

      let bPose = bRest;
      if (S.on) {
        bPose = mix(bRest, bReach, E.soft(seg(T, 1.5, 1.9)));
        bPose = mix(bPose, bCheer, E.back(seg(T, 2.5, 3.0)));
        bPose = mix(bPose, bRest, E.soft(seg(T, 4.7, 5.1)));
      }
      bPose = breathe(bPose, S.t + 1.1, 0.7);
      if (bGait) bPose = legs(bPose, bGait.ph, bGait.amp, { arms: false, stride: bGait.stride });

      fig(g, bPose, bx, 0, {
        sx: -1,
        ink: '#3d7a8c',
        far: '#a9c9d1',
        bot: { col: '#3d7a8c', dark: '#2a5866', glow: locked ? 1 : 0.3, blink: pulse(S.t, 4.1, 1.0, 0.14) > 0.5, happy: locked },
      });
      text(g, '18ms fiber', bx, 16, 8, '#3d7a8c');

      // Slow User (You) walks slower from -142 to -56, arrives at T=2.7 -> sees locked -> throws hands up
      let ux = -120, uGait = null;
      if (S.on && T < 2.75) {
        const ws = walkSeg(T, 0.2, 2.75, -138, -56);
        ux = ws.x;
        uGait = ws;
      } else if (S.on && T >= 2.75 && T < 5.0) {
        ux = -56;
      } else if (S.on && T >= 5.0) {
        const ws = walkSeg(T, 5.0, 5.9, -56, -120);
        ux = ws.x;
        uGait = { ph: -ws.ph, amp: ws.amp, stride: ws.stride };
      }
      const uReach = P({ chest: [5, -89], head: [9, -114], hF: [36, -90], hB: [-4, -52] });
      const uWhoa = P({ chest: [-3, -90], head: [-5, -116], hF: [14, -122], hB: [-12, -114] });
      let uPose = bRest;
      if (S.on) {
        uPose = mix(bRest, uReach, E.soft(seg(T, 2.55, 3.0)));
        uPose = mix(uPose, uWhoa, E.back(seg(T, 3.25, 3.65)));
        uPose = mix(uPose, bRest, E.soft(seg(T, 4.7, 5.1)));
      }
      uPose = breathe(uPose, S.t, 0.8);
      if (uGait) uPose = legs(uPose, uGait.ph, uGait.amp, { arms: false, stride: uGait.stride });
      fig(g, uPose, ux, 0, { sx: 1, ink: '#141414' });
      text(g, 'you (320ms)', ux, 16, 8, '#141414');

      if (S.on && T >= 3.2 && T < 4.9) {
        bubble(g, ux - 28, -142, 'WL 180!', 1, E.back(seg(T, 3.2, 3.55)), C.red, C.redInk);
      }
    },
  };
})();
