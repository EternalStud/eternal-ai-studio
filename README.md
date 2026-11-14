# Eternal AI Studio — Real-World AI Revenue Lab

> **Can an AI + Apple Mac Mini (M2) + Samsung M31 Edge Server actually produce public-grade work worthy of earning real money — or is "make money with AI" mostly hype?**  
> This repository is our transparent, evidence-driven laboratory to find out.

## Core Rules of This Lab
1. **Zero Teacher/Student Monetization:** All education/teacher tools on `uhskaparpurakanti.in` stay 100% free. This repo is strictly for **public media, digital products, and scalable creative assets**.
2. **Quality Gate First ("Worthy or Slop?"):** We never spam low-effort AI sludge. Every prototype is rendered end-to-end on the Mac Mini so the human operator can watch it and judge: *"Would I watch this, share this, or pay for this?"*
3. **Full Session Continuity:** Every experiment, render script, cost/revenue math, and blocker is logged in [`RESUME_HERE.md`](./RESUME_HERE.md) so any new session can continue seamlessly from the last commit.

## Hardware & Software Stack
- **Render Studio:** Apple Mac Mini (M2, 8 GB RAM) + Blender (`bpy` procedural 3D) + FFmpeg + `Final Cut Pro` + `Voicebox` / `Maono Link` + `edge-tts`
- **Burst Cloud GPU:** Google Colab T4/L4 (`colab-skill`) when heavy Cycles raytracing or ML exceeds 8 GB RAM
- **24/7 Edge Automation:** Samsung Galaxy M31 (Termux ARM64) for scheduling, analytics, and Telegram approval workflows

## Repository Structure
- `README.md` — Lab overview and rules
- `RESUME_HERE.md` — Living state tracker (what is built, rendered, verified, and next step)
- `STRATEGY_AND_MATH.md` — Honest unit economics of what earns vs what fails
- `scenes/` — Procedural Blender (`bpy`) Python scene builders
- `audio/` — Voice synthesis, sound effects (procedural/royalty-free), and timing/SRT alignment
- `compositor/` — FFmpeg assembly, kinetic subtitles, and Final Cut / YouTube export packaging
- `scripts/` — One-command pipeline runners
- `output/` — Local rendered MP4s & preview stills (`.gitignored` for large binaries)
