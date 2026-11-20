# Quality Standards & Lessons Learned (Anti-Slop Playbook)

> **Why most automated channels fail:** They force one template/tool onto every topic and ship static slide-deck visuals or unverified metrics.  
> **Our rule:** **Analyse the topic first**, match the visual engine to the story, animate continuously across every beat, and enforce visual-to-data truthfulness.

## Rule 0 — Topic-First Visual & Skill Selection (Mandatory Gate)
Before opening Blender, Playwright, or FFmpeg for any new video:
1. **Does this topic genuinely need 3D (`blender`)?**
   - **Use Blender 3D ONLY when physical spatial anatomy or tangible world storytelling adds clarity** (e.g., undersea cables, physical chip/core mechanics, architectural disasters) — never mix rough 2D stick figures into lit 3D worlds (`Episode 01` lesson).
   - **Do NOT force Blender 3D onto software/browser workflows or abstract/map/system topics** (e.g., `Google Colab`, `UDISE+`, routing graphs, telemetry flows) where **real zoomed screen recordings**, **archival photography (`POC #2`)**, or **bespoke frame-accurate HTML5 Canvas/SVG data animations** explain the idea 10× more clearly.
2. **Zero Repetitive Loops ("1 Beat = 1 Dedicated Visual"):**
   - Never reuse a handful of 4–8s boomerang clips or static dashboards across 20+ narration beats (`google_colab_masterclass_16x9.mp4` lesson).
   - Every narrative beat must drive its **own custom animated visual state** directly tied to what the narrator is saying.

## Rule 1 — Motion, Data Truthfulness & Layout Standards (Learned From `7.4/10` Audit)
1. **No Static "Slide-Deck" Beats:** Climax stories, privacy gates, and outros must animate data packets, progressive state transitions (`Green → Amber → Crimson`), highlighted stacking cards, and micro camera scale—never park a still dot or frozen card for 8–12 seconds.
2. **Strict Visual ↔ Data Consistency (Never Spoil Ahead of the Animation):**
   - Exact icon counts must match spoken/headline numbers (e.g., `"25 Phones"` renders **25 icons**, not 17 or 20).
   - Bind top HUD badges and threshold alerts to the animation progress `p`: never display `AVG: 12 KM/H` or `THRESHOLD HIT → RED` while the speedometer still shows `49 km/h`.
3. **Real Engineering Telemetry Details:**
   - All charts must render explicit **X-axis and Y-axis ticks & units** (e.g., `5:30 PM – 7:00 PM`, `0 – 60 km/h`).
   - Graph/network nodes must use **descriptive labels + directional flow arrows** (`Choke Point`, `Main Entry`, `Bypass`), never unlabelled abstract IDs (`J1–J6`).
   - Text labels over grids must sit inside **clean solid/frosted pill backdrops**; strikethrough graphics must avoid awkwardly bisecting icons/text.
4. **Break Layout Monotony Across Multi-Beat Explainers:**
   - Mix full-bleed map POVs, split-screen real-world vs. phone-UI comparisons, telemetry charts, and stacked card reveals rather than locking every beat into the exact same centered box mold.

## Production Gates Every Video Must Pass
1. **Immediate Hook (First 3 Seconds):** Drop the viewer into live visual motion + curiosity tension from Frame 1.
2. **Approved Dual-Voice Pipeline:**
   - **Male Primary Narrator:** `ChatterboxMultilingualTTS` (`Notebook LLM hindi` voice profile, generated cleanly on GPU) OR creator's cleaned real mic voice (`udise_automation_master_edited.mp4` FFmpeg chain). Never use `edge-tts` synthetic voices.
   - **Female Co-Host Interrupts:** `maya-research/Veena` **`kavya`** for sharp viewer doubts and key takeaways.
   - **Trimming:** Always trim trailing silence using **RMS amplitude scanning** (+140ms breath pad + fadeout) — never hard-slice fixed milliseconds off the tail.
3. **Audio & Caption Polish:** Crisp `Kohinoor Devanagari` subtitles cleanly anchored in safe zones + stereo ambient bed & radar/ping SFX mastered to **`-14 LUFS`**.
4. **Spot Inspection + Post-Export Verification:** Always inspect spot frames (`read_file`) *across dynamic progress timestamps* before full rendering, plus final MP4 frames & audio clips before publishing.
