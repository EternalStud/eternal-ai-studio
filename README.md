# Eternal AI Studio — Real-World AI Revenue Lab

> **Can an AI + Apple Mac Mini (M2) + Samsung M31 Edge Server actually produce public-grade work worthy of earning real money — or is "make money with AI" mostly hype?**  
> This repository is our transparent, evidence-driven laboratory to find out.

## Core Rules of This Lab
1. **Zero Teacher/Student Monetization:** All education/teacher tools on `uhskaparpurakanti.in` stay 100% free. This repo is strictly for **public media, digital products, and scalable creative assets**.
2. **Quality Gate First ("Worthy or Slop?"):** We never spam low-effort AI sludge. Every prototype is rendered end-to-end on the Mac Mini so the human operator can watch it and judge: *"Would I watch this, share this, or pay for this?"*
3. **Full Session Continuity:** Every experiment, render script, cost/revenue math, and blocker is logged in [`RESUME_HERE.md`](./RESUME_HERE.md) so any new session can continue seamlessly from the last commit.

## Hardware & Software Stack
- **Render Studio:** Apple Mac Mini (M2, 8 GB RAM) + Blender `5.3.0` (`bpy` procedural 3D / `BLENDER_EEVEE`) + Brave Headless + Playwright (HTML5/CSS3D & transparent RGBA glass HUD overlays) + FFmpeg (`loudnorm -14 LUFS`, `libx264`) + `Final Cut Pro` + `Voicebox` / `Maono Link` + `edge-tts==7.3.1`
- **Burst Cloud GPU:** Google Colab T4/L4 (`colab-skill`) when heavy Cycles raytracing or ML exceeds 8 GB RAM
- **24/7 Edge Automation:** Samsung Galaxy M31 (Termux ARM64) for scheduling, analytics, and Telegram approval workflows

## Repository Structure
- `README.md` — Lab overview and rules
- `RESUME_HERE.md` — Living state tracker (all POCs, visual QA findings, gotchas, and next steps)
- `STRATEGY_AND_MATH.md` — Honest unit economics & format insights (`90–150s` depth, RPM math)
- `scenes/` — Procedural Blender (`bpy`) Python scene builders & HTML5/CSS3D/HUD stages
- `audio/` — Word-boundary TTS synthesis (`edge-tts`), silence trimming, and procedural stereo SFX
- `compositor/` — FFmpeg assembly, Playwright deterministic frame renderer, and Blender+HUD RGBA overlay compositor
- `assets/` — Curated archival imagery (`nyse_facade.jpg`, etc.)
- `scripts/` — One-command pipeline runners (`run_poc1_full.py`, `run_poc2_full.py`, `run_poc3_full.py`)
- `output/` — Local rendered MP4s (`.gitignored` for large binaries)
