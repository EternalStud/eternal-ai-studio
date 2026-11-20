# Quality Standards & Lessons Learned (Anti-Slop Playbook)

> **Why most automated channels fail:** They force one template/tool onto every topic and stretch repetitive visuals over long narration.  
> **Our rule:** **Analyse the topic first**, choose *only* the visual medium and skills that authentically serve that topic, and make every beat visually distinct before exporting.

## Rule 0 — Topic-First Visual & Skill Selection (Mandatory Gate)
Before opening Blender, Playwright, or FFmpeg for any new video:
1. **Does this topic genuinely need 3D (`blender`)?**
   - **Use Blender 3D ONLY when physical spatial anatomy or tangible world storytelling adds clarity** (e.g., undersea cables, physical chip/core mechanics, architectural disasters) — and never mix rough 2D stick figures into lit 3D worlds (`Episode 01` lesson).
   - **Do NOT force Blender 3D onto software/browser workflows or abstract/map/system topics** (e.g., `Google Colab`, `UDISE+`, routing graphs, financial crashes) where **real zoomed screen recordings**, **archival photography (`POC #2`)**, or **bespoke frame-accurate HTML5 Canvas/SVG data animations** explain the idea 10× more clearly and authentically.
2. **Zero Repetitive Loops ("1 Beat = 1 Dedicated Visual"):**
   - Never reuse a handful of 4–8s boomerang clips or static dashboards across 20+ narration beats (`google_colab_masterclass_16x9.mp4` lesson).
   - Every narrative beat must drive its **own custom animated visual state** directly tied to what the narrator is saying at that exact second.

## Production Gates Every Video Must Pass
1. **Immediate Hook (First 3 Seconds):** Drop the viewer into a concrete mystery, real-world failure, or counter-intuitive claim with live motion from Frame 1.
2. **Approved Dual-Voice Pipeline:**
   - **Male Primary Narrator:** `ChatterboxMultilingualTTS` (`Notebook LLM hindi` voice profile, generated cleanly on GPU) OR user's cleaned real mic voice (`udise_automation_master_edited.mp4` FFmpeg chain). Never use `edge-tts` synthetic voices.
   - **Female Co-Host Interrupts:** `maya-research/Veena` **`kavya`** for sharp viewer doubts/questions.
   - **Trimming:** Always trim trailing silence using **RMS amplitude scanning** (+140ms breath pad + fadeout) — never hard-slice fixed milliseconds off the tail.
3. **Typography & Subtle HUD:** Clean native `Kohinoor Devanagari` subtitles cleanly anchored without blocking hero visuals; subtle stereo ambient bed + crisp beat SFX mastered to **`-14 LUFS`**.
4. **Spot Inspection Before Final Delivery:** Always inspect extracted video frames (`read_file`) AND listen to audio segments (`read_file`) after final muxing.
