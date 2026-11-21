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

---

### Episode 01 — `ep01_tatkal_concurrency` (COMPLETE — Universal 3-Engine CS Flagship)
- **Topic & Target Audience:** *IRCTC 10:00 AM Tatkal — Million-to-One Concurrency Funnel* (Computer Science, Age 16–36)
- **Output:** `output/ep01_tatkal_concurrency_1080x1920.mp4` (`40M`, `113.25s` @ `24fps`, `2718 frames`, `2219.1s` / ~37 min total sequential M2 build)
- **Core Universal Studio Architecture Added (`engine/`, `config/`):**
  - `engine/blender_studio_kit.py`: Cross-version Blender 4.2/5.3 safe compositor (`Bloom` glare, `ShaderNodeVolumeScatter`), procedural `Noise → Bump` PBR materials, and `animate_shot_clamped()` (`CONSTANT` cuts at `f_next_cut - 1`, zero camera fly-across verified via `cut_test_0429.png` → `cut_test_0430.png`).
  - `engine/vendor_stick.js` & `engine/stick_scenes_tatkal.js`: MIT-vendored procedural stick-figure rig (`nilbuild/stick-scene`) with deterministic `STICK.at()` seeking for human drama (`tatkal_typing_panic` at `09:59:58` & `tatkal_mutex_race` between `you (320ms)` and `18ms fiber`).
  - `engine/universal_hud.html`: Strict 5-zone `1080×1920` grid (`Zone A` chronometer + `AVL 042 → WL 180`, `Zone B` stick-card & tilted CSS3D SQL/Cache/Gate cards, `Zone C` telemetry + verified source citation, `Zone D` 4-word gold-highlighted Hinglish captions, `Zone E 1680–1920px` clear).
  - `config/pronunciation_lexicon.json` + `audio/tts_and_captions.py`: Phonetic Devanagari lexicon mapping (`IRCTC`, `CRIS`, `SQL`, `Mutex`, `Redis`, `OTP`, `CAPTCHA`) while preserving crisp technical spelling in synced captions.
  - `engine/qa_auditor.py`: Automated `DOM_QA` (`IoU == 0.0`, zero Zone-E leakage), `PIXEL_QA`, and `POST_QA` (`1080×1920`, `duration_s: 113.25`, `lufs: -14.6`, `true_peak_dbfs: -1.3`, `passed: true`).
- **Verified:** Spot frames (`--spot-only`), cut boundary frames, and final MP4 frames (`v10.png`, `v66.png`, `v96.png`) all visually inspected cleanly.
- **User Feedback (Episode 01 Rejected):** Mixing `stick-scene` + 3D scenes looked ugly; pivoted to editing the user's real Final Cut Pro UDISE+ screen recording (`input/`).

---

### UDISE+ Automation Tutorial Edit & Voicebox Hindi Short (COMPLETE)
- **Raw Input:** `input/udise+ automation GP, PEN search , Udise Import.mov` (`613.4 MB`, `1920×960 @ 60fps`, `1031.63s` / `17m 11s`)
- **Deliverable 1 — Full Master Edited Tutorial (`scripts/edit_udise_pro_master.py`):**
  - **Output:** `output/udise_automation_master_edited.mp4` (`62.3 MB`, `1920×1080 @ 60fps`, `760.29s` / `12.65m`, `-14.1 LUFS`)
  - **Voice:** Preserved user's genuine human voiceover (rejected robotic `edge-tts`) with broadcast vocal EQ + noise reduction (`highpass=85, lowpass=12500, afftdn=nf=-24, acompressor, loudnorm=-14`).
  - **Edits & Privacy:** Moved `"724 students updated in 30 mins"` social-proof hook to `00:00`, cut giant `"Join telegram Channel"` text overlay (`15.5–26.0s`), static PDF monologue (`16.5–142.5s`), server/RAM monologue (`219.5–262.0s`), login-fail stumble (`422.5–441.5s`), Inspect fumble (`659.5–665.8s`), and summer-vacation outro (`998.0–1031.6s`); zoomed `1920×1080` to strip macOS bar/pillars; blurred sensitive `UDISE Code`, `JSESSIONID`, `School ID` URL, `COOKIE_HEADER`, and `ENCRYPT_KEY`; added lower-third chapter & Telegram banners.
- **Deliverable 2 — Vertical YouTube Short (`scripts/render_udise_short_voicebox.py` + `scenes/udise_short_hud.html`):**
  - **Output:** `output/udise_automation_yt_short_1080x1920.mp4` (`2.5 MB`, `1080×1920 @ 30fps`, `38.50s`, `-14.9 LUFS`)
  - **Voice:** Local **Voicebox `chatterbox`** Hindi voice (`Notebook LLM hindi` profile, cached in `~/.cache/huggingface/hub/models--ResembleAI--chatterbox`) with `-450ms` tail puff trimming and `-14 LUFS` mastering.
  - **Visuals & Privacy:** Frosted glass HUD over zoomed portal/Colab/DevTools screen clips with synced 4-word gold-highlighted Hindi captions and `avgblur` over both `JSESSIONID` and `UDISE Code`.

---

### Google Colab 6-Minute 16:9 Masterclass & Blender Lab MCP Skill (COMPLETE)
- **Output:** `output/google_colab_masterclass_16x9.mp4` (`195.8 MB`, `1920×1080 @ 24fps`, `366.40s` / `6m 06s`, `-14 LUFS`, 28 dialogue beats)
- **Blender Lab MCP & Project Skill:**
  - Installed official `lab_blender_org/mcp` (`v1.0.3`, `localhost:9876`) in Blender 5.3.0, synced `projects.blender.org/lab/blender_mcp` (`v1.0.2`) to `/Volumes/Eternal T7/PROJECT/blender_mcp`, configured `/Users/eternalstudent/.gemini/config/mcp_config.json`, and wrote `.agents/skills/blender/SKILL.md`.
- **Voices & Audio Mastering (`scripts/build_colab_audio.py`):**
  - **Male Primary Host (25 beats):** `ChatterboxMultilingualTTS` cloned from `Notebook LLM hindi`, synthesized on Google Colab T4 (`colab-audio`), trimmed via RMS trailing-silence detection (`+140ms` breathing pad—zero clipped final syllables).
  - **Female Co-Host Interrupts (3 beats):** `maya-research/Veena` **`kavya`** (`b03`, `b15`, `b21`) synthesized on Google Colab T4 (`colab-bench`).
  - Mixed with stereo ambient SFX (`audio/sfx_gen.py`) and mastered to `-14 LUFS`.
- **Visual Architecture (`scenes/colab_hero_worlds.py`, `scenes/colab_motion_ui.html`, `scenes/colab_hud_16x9.html`, `scripts/build_colab_video.py`):**
  - 5 Blender 5.3 3D hero clips (`w1_oom`, `w1_ok`, `w2_dc`, `w3_cpugpu`, `w4_vault`) with crisp Playwright display textures (`scripts/generate_screen_textures.py`) and visually inspected previews (`w1_desk..w4_vault`).
  - 4 interactive `1920×1080` animated UI scenes incorporating authentic verified Colab T4 benchmark numbers (`4096×4096 FP32 ×15`: **CPU `17.94s` vs Tesla T4 `0.522s`, `34.4× faster`**).
  - Verified final output frames (`v_10..v_295`) and audio slices (`a_24_42.mp3`, `a_end.mp3`).
- **Human Feedback Verdict (Critical Mandate):**
  - **Voice Approved:** *"Voice is awesome."* Dual-voice **`Notebook LLM hindi` (Chatterbox) + `Veena kavya`** cleanly passed human review.
  - **Visuals Critique:** Repeating 5 short 3D boomerang loops + 4 UI templates across 28 beats felt repetitive and disconnected from the explainer.
  - **New Studio Rule Across All `.md` Files:** **Analyse the topic FIRST** to decide which skills/visuals are needed (never force Blender 3D onto topics better served by bespoke Canvas/SVG motion graphics or zoomed screen recordings), and enforce **1 beat = 1 bespoke animated visual**.

## Next Steps
1. **Google Maps 2-Minute Explainer `v2` (COMPLETE — Visually Verified & Staged on `Decode Systems`):**
   - **Final Output:** `output/gmaps_traffic_2min_1080x1920.mp4` (`26.7 MB`, `1080×1920 @ 30fps`, `135.25s` / `4,058` frames, `-14 LUFS`, dual-voice `Chatterbox Notebook LLM hindi` + `Veena kavya`).
   - **Critique Fixes Verified via Extracted MP4 Frames (`f_3s.png`, `f_24s.png`, `f_46s.png`, `f_82s.png`):**
     - Replaced static slide-deck beats (`t03`, `t08`, `t09`, `t12`) with continuous opaque-gate packet anonymization flow (`Rahul +91...` → `Hash #9F3A ✓`), split-screen Berlin cart + live `Green → Amber → Crimson` phone map UI, and staggered 3-pillar card reveal + Ghost Jam comment prompt.
     - Fixed exact count/telemetry sync (`25` phone icons in `t05`, live top-right `LIVE: XX KM/H` pill + `CONGESTION BUILDING...` threshold synced to gauge needle `50 → 12 km/h`), explicit `5:30–7:00 PM` & `0–60 km/h` axes (`t06`), descriptive graph nodes + directional flow arrows (`t07`), frosted pill backing (`t02`), and full-bleed highway POV (`t01`).
2. **Multi-Channel YouTube Bridge & Autonomous `Decode Systems` Launch (`automation/youtube_bridge.py`):**
   - **Channel Separation Enforced:**
     - `Eternal Student` (`@Etrnll0v` / `UCU7tyDOES8n9XqIDJ86gSrQ`): User's co-managed teacher/school portal automation channel.
     - `Decode Systems` (`decode_systems` alias -> `UCqhU754GdfiB-1IVQFmem6g`, aged `2012-01-02`, formerly `Eternal Love`): Autonomous tech/AI/systems channel targeting YPP monetization (`1,000` subs + `4,000` watch hours).
   - **Completed Channel Setup & Staged Launch:**
     - Pushed `Decode Systems` description, keywords, `country="IN"`, and `defaultLanguage="hi"` via `channels.update`.
     - Generated `800×800` avatar (`assets/decode_systems_avatar.png`) and `2560×1440` banner (`assets/decode_systems_banner.png`) and documented full pipeline in `docs/CHANNEL_DECODE_SYSTEMS.md`.
     - Stage-uploaded Episode #1 (`v2`) onto `decode_systems` as a `private` draft: **Video ID `Dd3bUHJ73VU`** (`https://www.youtube.com/watch?v=Dd3bUHJ73VU`).
3. **Immediate Next Actions:**
   - Complete the one-time 15-second YouTube Studio UI update on `UCqhU754GdfiB-1IVQFmem6g` (Name → `Decode Systems`, Handle → `@decodesystems_in`, upload `decode_systems_avatar.png` + `decode_systems_banner.png`), then set `Dd3bUHJ73VU` to Public.
   - Produce **Episode #2** (`16:9` 6-min Deep Dive + paired 2-min Short hook per `docs/CHANNEL_DECODE_SYSTEMS.md`) to start stacking watch hours + subscribers together.
