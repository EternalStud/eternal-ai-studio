# Quality Standards & Lessons Learned (Anti-Slop Playbook)

> **Why most automated channels fail:** They connect APIs too early and scale mediocre videos.  
> **Our rule:** Never scale a template until a single video passes the human "Would I actually watch and share this?" test.

## Mistakes Other AI Channels Make (That We Refuse to Repeat)
1. **Static visuals / slow hooks:** Viewers swipe away in 1.8 seconds if nothing moves or surprises them in Frame 1–45.
   - *Our fix:* Immediate visual contrast + motion in the first 0.5s + camera beat shift every 2–4 seconds.
2. **Pure "primitives in Blender" look:** Untextured boxes floating in space look amateur.
   - *Our fix:* Composite **two layers** in V2+:
     - **Layer 1 (Blender `bpy`):** 3D studio lighting, `AgX` tone mapping, reflective obsidian/metal shaders, smooth Bezier camera rigs, particle/shockwave motion.
     - **Layer 2 (Playwright/SVG Transparent HUD Overlays):** Crisp glassmorphic callout cards, animated counters (`0.00s -> 0.80s`), arrows, and data badges composited over the 3D render via FFmpeg.
3. **Flat robotic audio:** TTS alone feels empty.
   - *Our fix:* Subtle sub-bass ambient bed + beat impact hits + ascending node-pings + `-14 LUFS` broadcast loudness normalization. Later: upgrade voice via **Voicebox** or **Maono Link** human voiceover.
4. **Uploading before reviewing:** Blind auto-publishing hurts channel trust score with the YouTube/IG algorithm.
   - *Our fix:* Always inspect rendered stills + watch the full MP4 locally (and route through Telegram `[Approve / Regenerate / Discard]` once automated).
5. **Chasing Shorts RPM alone:** Indian Shorts pay pennies per 1K views.
   - *Our fix:* Shorts/Reels are the **top-of-funnel discovery engine**. Every 4 related Shorts feed into **8–12 min 16:9 English Deep-Dives** + **downloadable Gumroad `.blend` / template packs**.
