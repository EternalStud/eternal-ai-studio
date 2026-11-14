# RESUME HERE — Session Continuity & Experiment Ledger

> **Always read this file first when starting a new session on any machine.**

## Current Status (2026-11-14)
- **Dedicated Repository Created:** `/Volumes/Eternal T7/PROJECT/eternal-ai-studio` (branch `main`)
- **Blender Installed:** Blender `5.3.0` via Homebrew Cask (`/Applications/Blender.app`, `/opt/homebrew/bin/blender`)
- **Python Audio Environment:** `.venv` with `edge-tts==7.3.1` (note: `edge-tts` requires `boundary="WordBoundary"` in v7.3+ to emit word timestamps)

## Active Proof-of-Concept: POC #1 (`upi_vs_banks_3d`)
**Thesis tested:** Can AI + Apple Mac Mini M2 (8 GB) + Blender `bpy` + procedural sound design produce a **studio-grade 1080×1920 3D explainer Short** (not generic AI slop) at ₹0 cloud cost?

### Pipeline Built
1. **Beat-Locked Narration & Kinetic Captions:** [`audio/tts_and_captions.py`](./audio/tts_and_captions.py)
   - Synthesizes each story beat individually (`en-US-AndrewMultilingualNeural`), measures exact millisecond durations, concatenates with `adelay`, and outputs word-level highlighted `.ass` captions.
2. **Procedural Royalty-Free Sound Design:** [`audio/sfx_gen.py`](./audio/sfx_gen.py)
   - Pure Python stereo WAV synthesis: subtle dark ambient sub-drone, beat-transition sub-bass hits + air whooshes, and 4 ascending musical node-pings locked to packet arrival timestamps.
3. **Procedural Blender 5.3 3D Scene:** [`scenes/upi_vs_banks_3d.py`](./scenes/upi_vs_banks_3d.py)
   - EEVEE studio lighting + `AgX` tone mapping + Compositor `Fog Glow` bloom.
   - Left Zone: Open-cage Legacy Batch Vault with beveled gold bullion bars & animated crimson laser barriers (`2 DAYS`).
   - Right Zone: 4-node curved Instant Rail (`PHONE` → `APP NODE` → `NPCI SWITCH` → `RECEIVER`) with spinning halos, fiber-optic conduit, traveling packet sphere, expanding shockwave rings, and emerald settlement flash (`0.8 SEC`).
   - Also saves reusable `.blend` scene (`tmp/poc1_upi/upi_vs_banks_3d.blend`).
4. **Master FFmpeg Compositor:** [`compositor/assemble_video.py`](./compositor/assemble_video.py)
   - Compresses/levels voice (`highpass` + `acompressor`), mixes SFX, normalizes to `-14 LUFS`, burns kinetic `.ass` subtitles, and encodes H.264 `+faststart` MP4.
5. **One-Command Runner:** [`scripts/run_poc1_full.py`](./scripts/run_poc1_full.py)

### Visual QA Performed
- Rendered 4 hero stills at `540×960` and `1080×1920` (`~3.6–4.7s` total!).
- Caught & fixed: opaque transmission glass hiding bullion bars, 36mm framing clipping inside 9:16 vertical, `0.8 SEC` vs `NPCI SWITCH` label overlap, and `edge-tts` v7.3 `WordBoundary` flag.
- Full `1080×1920 @ 24fps` render (`~855` frames, `~0.75s/frame`) + FFmpeg assembly triggered via:
  ```bash
  .venv/bin/python3 scripts/run_poc1_full.py --mode anim --res 1080x1920 --fps 24 --samples 12
  ```
- Output target: `output/poc1_upi_vs_banks_1080x1920.mp4`

## Next Steps (Pending Human Critique)
1. Watch `output/poc1_upi_vs_banks_1080x1920.mp4` and evaluate honestly against the 4 gates in [`STRATEGY_AND_MATH.md`](./STRATEGY_AND_MATH.md).
2. Upgrade voice to **Voicebox** (`/Applications/Voicebox.app`) or **Maono mic** human recording if desired for maximum authenticity.
3. If POC #1 passes quality bar:
   - Link GitHub remote (`https://github.com/EternalStud/eternal-ai-studio.git`) and push `main`.
   - Test **Productization**: package reusable `bpy` scene presets + render 3 high-RPM episodes + evaluate **Gumroad `.blend`/template pack** + **YouTube Shorts → Long-form** launch.
