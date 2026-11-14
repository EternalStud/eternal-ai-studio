# RESUME HERE — Session Continuity & Experiment Ledger

> **Always read this file first when starting a new session on any machine.**

## Current Status (2026-11-15)
- **Dedicated Repository:** `/Volumes/Eternal T7/PROJECT/eternal-ai-studio` (`origin`: `https://github.com/EternalStud/eternal-ai-studio.git`, branch `main`)
- **Verified Local Toolchain (Apple M2 Mac Mini, 8 GB RAM):**
  - **3D Engine:** Blender `5.3.0` (`BLENDER_EEVEE`, `AgX`, `CompositorNodeGlare`)
  - **2D / Glass HUD / Motion Engine:** Playwright + `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser` (supports both opaque HTML5/CSS3D/Canvas docs AND `omit_background=True` 32-bit transparent RGBA HUD overlays)
  - **Voice & Captions:** `.venv` with `edge-tts==7.3.1` (`boundary="WordBoundary"`, Indian voices tested: `hi-IN-MadhurNeural`), trimmed cleanly per beat via FFmpeg `atrim`
  - **Audio/Video Mastering:** Pure-Python stereo SFX generator (`audio/sfx_gen.py`) + FFmpeg `highpass`/`acompressor`/`amix`/`loudnorm=-14 LUFS` + `libx264` `+faststart`

---

## Experiment Ledger & Everything Learned So Far

### POC #1 — `upi_vs_banks_3d` (REJECTED — Critical Baseline Lessons)
- **Output:** `output/poc1_upi_vs_banks_1080x1920.mp4` (`26M`, `35.5s` @ `24fps`, `~11 min` render)
- **Files:** `scenes/upi_vs_banks_3d.py`, `scripts/generate_audio_poc1.py`, `scripts/run_poc1_full.py`
- **Human Feedback (Reject Verdict):**
  > *"Very poor, nobody will ever watch this... no storytelling, looks like a very beginner made it. Audio seems quite fancy English."*
- **Why it failed (root causes captured):**
  1. **No real-world story or human stakes:** Glowing Blender cubes/cylinders floating in darkness feel generic and beginner-made.
  2. **Wrong voice/language fit:** Formal US English (`en-US-AndrewMultilingualNeural`) feels detached and artificial for our target viewers.
  3. **No visual world or curiosity hook:** Abstract labels alone fail to hold attention.

---

### Gold Quality Benchmark Discovered — `output/Facebook.mp4` (`@fewshot.studio` — *Isse Kehte Hain · 003*)
- **Specs:** `1080×1920`, `30fps`, `154.57s` (`2m 34s`), `49M`
- **What makes it genuinely worthy & watchable (inspected audio + 8 keyframes):**
  1. **Lived-In 3D Worlds (Not Abstract Primitives):** Opens 3 km beneath the Arabian Sea floor with an illuminated submarine optical cable, then cuts to a warm Diwali balcony (diyas, rangoli, marigold toran, skyline lights, hand holding an iPhone).
  2. **One Unifying Slow-Motion Hook:** Persistent top header + live `0000.0 ms → 1000.0 ms` (`100× slow`) millisecond pill anchors the entire story in bullet-time.
  3. **Physical Metaphors Before Jargon:** Shows physical locked data, 1,390 numbered floating 3D cubes, visible Wi-Fi wave arcs, dark 3D network routing globe (`London this way`), packet assembly wall (`mil gaya!`), and reveals the technical 7-layer diagram only as the climax payoff.
  4. **Warm, Unhurried Hindi Storytelling + Clean Floating Callouts:** Calm, intimate conversational Hindi rather than loud/rushed hype; clean floating glass labels instead of big karaoke subtitle boxes blocking the 3D artwork.
  5. **Longer Format Works Better (`~150s`):** Gives viewers room to genuinely understand *how* and *why* something works.

---

### POC #2 — `knight_capital_doc` (PASSED Visual & Story Leap; Needs Longer Depth)
- **Output:** `output/poc2_knight_capital_1080x1920.mp4` (`14M`, `48.3s` @ `30fps`, `341.4s` total build)
- **Files:** `scenes/knight_capital_doc.html`, `compositor/html_motion_renderer.py`, `scripts/generate_audio_poc2.py`, `scripts/run_poc2_full.py`, `assets/nyse_facade.jpg`
- **Architecture:** Pure HTML5 + CSS 3D Perspective + Canvas real-time crash chart + real archival NYSE photography + documentary alarm/ticker SFX + conversational Hindi (`hi-IN-MadhurNeural` `+20%`) with native `Kohinoor Devanagari` word-highlighted captions.
- **Human Verdict:**
  > *"POC #2 is quite impressive progress. We need to make a bit longer video to give full understanding to the user too."*
- **Key Lesson:** Keep story beats unhurried (`90s–150s`) when teaching real systems/events so the viewer walks away with deep understanding, not a rushed summary.

---

### POC #3 — `chai_tapri_upi_800ms` (COMPLETE — Ready for Human Review)
- **Output:** `output/poc3_chai_tapri_upi_800ms.mp4` (`31M`, `64.70s` @ `24fps`, `1555 frames`, `1451.1s` / ~24 min total build on M2)
- **Files:**
  - `scenes/upi_tapri_3d.py` — 5 separated Blender 3D worlds along `X = 0, 60, 120, 180, 240`:
    1. Subterranean city optical fiber (`~5 ft deep`) with streaking light pulse orb + ring.
    2. Rainy evening roadside **Chai Tapri counter** (brass kettle, tea tray, 2 chai glasses, hanging warm tungsten bulb, 7×7 mini QR standee, green Soundbox, scanning phone + green laser, city window bokeh).
    3. Macro `15×15` 3D **QR Matrix** with corner finder eyes, amber chai-spill puddle, sweeping scan bar, and glowing Reed-Solomon parity recovery blocks.
    4. City rooftops + phone RSA/hardware padlock ring + expanding golden RF wave arcs hitting a red-beacon telecom tower.
    5. Midnight cyber-grid horizon + 3 hero bank/switch towers (`Your Bank`, `NPCI Switch`, `Chaiwala Bank`) connected by illuminated fiber conduits + circling verification orb.
    6. Hero return to Soundbox (expanding 3D emerald wave rings + sky beam) + elevated 5-layer ring stack finale.
  - `scenes/upi_tapri_hud.html` & `compositor/hybrid_overlay.py` — Transparent RGBA overlay (`omit_background=True`) rendering `AISE KAAM KARTA HAI · 001`, `@eternal.ai.studio`, live `0000.0 ms → 0800.0 ms` (`100× slow`) counter, contextual callouts, and 5-layer stack without cluttering the bottom of the frame.
  - `scripts/generate_audio_poc3.py` — Calm, warm Hindi narration (`hi-IN-MadhurNeural`, `rate="+8%"`, `pitch="-3Hz"`, `gap_ms=260`) + atmospheric C2/G2 pad + Soundbox C6-E6 dual chime.
  - `scripts/run_poc3_full.py` — End-to-end 3-stage runner.
- **Verified:** Inspected 7 composited spot frames (`comp_00..comp_06`) AND final MP4 frames (`v14.png`, `v43.png`, `v60.png`).

---

## Technical Gotchas & Pipeline Best Practices Learned
1. **`edge-tts==7.3.1` Silence Tail:** Always use `boundary="WordBoundary"` and trim MP3 trailing digital silence (`~900ms`) at `cues[-1].end_ms + 160ms` inside `audio/tts_and_captions.py`, otherwise beats drag with dead air.
2. **Blender 5.3 Multi-Scene Cuts:** Set `CONSTANT` interpolation on keyframes right before cut boundaries (`(fr + 1) in cut_frames`) and `BEZIER` inside shots so the camera cuts cleanly between separate 3D environments (`X = 0 -> 60 -> 120...`) without flying across space.
3. **Fast Clean EEVEE on M2 (8 GB RAM):** Keep `taa_render_samples = 16`, `use_raytracing = False`, use smooth-shaded opaque/metallic rim glass (`alpha=1.0`) instead of semi-transparent EEVEE alpha transmission to avoid speckle noise, and **always run `--spot-only` (`~15s`) to inspect every scene before full multi-minute renders**.
4. **Devanagari Typography:** Render Hindi text cleanly in Brave/Chromium using `Kohinoor Devanagari` rather than FFmpeg `libass` fallback fonts, avoiding glyph/matra shaping glitches.

---

## Next Steps (When User Returns After Watching POC #3)
1. **User Reviews POC #3** (`output/poc3_chai_tapri_upi_800ms.mp4`) and decides the winning visual format:
   - Hybrid **Blender 3D + Glass HUD** (POC #3 style),
   - **HTML5/CSS3D Documentary** (POC #2 style), or
   - **Combined Best-of-Both** (Blender 3D physical scenes + HTML documentary diagrams/maps/code-cards in one cohesive timeline).
2. **Scale Flagship Episode #1 to `90s–150s` (`1.5–2.5 min`)**: Expand narrative depth so viewers get complete conceptual clarity (matching [Facebook.mp4](file:///Volumes/Eternal%20T7/PROJECT/eternal-ai-studio/output/Facebook.mp4)'s `154.6s` depth).
3. **Voice Upgrade Check:** Test human narration via user's **Maono mic** or tuned **Voicebox** Hindi clone vs `hi-IN-MadhurNeural` (`+6%`..`+8%`) before public channel launch.
4. **Distribution Gate (Still Held Until Quality Approved):** Only connect YouTube / Instagram / Facebook publishing once the flagship `90–150s` episode clears all quality gates.
