# Channel Playbook: Decode Systems (`decode_systems`)

**Owned & Operated Autonomously by Eternal AI Studio**
**Monetization Target:** YouTube Partner Program (`1,000 Subscribers` + `4,000 Public Watch Hours` in 12 months, or `10M` Shorts views)

---

## 1. Channel Identity & Separation Policy

| Attribute | Value |
|---|---|
| **Channel Name** | **Decode Systems** (renaming legacy channel `Eternal Love`) |
| **Channel ID** | `UCqhU754GdfiB-1IVQFmem6g` (created `2012-01-02`, aged account, `longUploadsStatus: eligible`) |
| **Registry Alias** | `decode_systems` in `credentials/channels.json` |
| **Target Handle** | `@decodesystems_in` |
| **Format & Language** | Hinglish Narrative + English Visual Telemetry HUDs (Dark-Mode Tech Aesthetic) |
| **Voice Cast (Locked)** | Male Host (`ChatterboxMultilingualTTS` / `Notebook LLM hindi`) + Female Co-Host (`maya-research/Veena` / `kavya`) |
| **Sibling Channel** | `Eternal Student` (`@Etrnll0v` / `UCU7tyDOES8n9XqIDJ86gSrQ`) stays strictly dedicated to teacher/school portal automation & free utilities for `uhskaparpurakanti.in`. |

### Programmatic vs. Manual Studio Setup
- **Already Pushed via YouTube Data API v3 (`channels.update`):**
  - Channel Description, Channel Keywords (`"Tech Explained"`, `"How It Works"`, `"System Design"`, `"AI Hinglish"`, `"Google Maps"`, `"Computer Science"`, `"Eternal Studio"`), Country (`IN`), Default Language (`hi`).
- **One-Time 15-Second Action in YouTube Studio (API Restriction):**
  YouTube Data API v3 does not permit changing `snippet.title`, `customUrl` handle, profile avatar, or channel banner programmatically. In **YouTube Studio → Customization → Basic info / Branding**:
  1. **Name:** `Decode Systems`
  2. **Handle:** `@decodesystems_in`
  3. **Profile Picture:** Upload `assets/decode_systems_avatar.png` (`800×800`)
  4. **Banner Image:** Upload `assets/decode_systems_banner.png` (`2560×1440`, safe center `1546×423`)

---

## 2. Two-Engine YPP Monetization Strategy

Pure Shorts channels hit `1,000` subscribers quickly but struggle to hit `10M` Shorts views or earn high AdSense RPM. Pure `16:9` channels earn watch hours fast but grow subscribers slower from zero. **Decode Systems pairs both on every major topic:**

1. **Top-of-Funnel Acquisition (`1080×1920`, ~2 mins / `<60s` hooks):**
   - Purpose: High-velocity subscriber conversion + comment engagement.
   - Format: Tight 12-beat visual explainers (dark-mode telemetry, kinetic diagrams, live synced counters, Hinglish captions).
2. **Watch-Hour & RPM Engine (`1920×1080` `16:9`, 6–8 mins):**
   - Purpose: Accumulate **`4,000` watch hours** via YouTube Search & Suggested Browse (`India Tech / Edutainment` + NRI audience).
   - Format: Deep-dive architecture breakdowns linking back from the paired Short via Pinned Comment + End Screen.

---

## 3. Initial 10-Episode Content Pipeline

| Ep | Title Concept | Primary Visual Engine (Topic-First) | Target Format |
|---|---|---|---|
| **01** | **How Google Maps Predicts Traffic Before Anyone Brakes (+ 99 Phones Hack)** | 2D Canvas Live Telemetry, Anonymizer Packet Shredder, Graph Propagation, Berlin Split-Screen (`v2`) | 2-Min Vertical (`v2` Staged) + 6-Min `16:9` |
| **02** | **Why YouTube Never Buffers on 4G (ABR Streaming & Edge CDN Hops)** | Animated Packet Pipeline, Buffer Watermark Graph, Resolution Bitrate Ladder | 6-Min `16:9` + 2-Min Cut |
| **03** | **Where Does Your 2–3% Credit Card Fee Actually Go in 1.4 Seconds?** | Split-Second Ledger Flow (`Merchant → Acquirer → Visa/NPCI → Issuer`), Kinetic Coin Split | 2-Min Vertical + 6-Min `16:9` |
| **04** | **How WhatsApp End-to-End Encryption Hides Chats Even From Meta** | Signal Protocol Key Exchange Animation, Asymmetric Lock + Double Ratchet Simulator | 6-Min `16:9` + 2-Min Cut |
| **05** | **How GPS Pinpoints You in 3m Using 4 Satellites + Einstein's Relativity** | Blender 3D Orbital Constellation + 2D Nanosecond Drift HUD (Dual-Engine Justified!) | 6-Min `16:9` + 2-Min Cut |
| **06** | **Why Airplane Wi-Fi Works at 35,000 ft (LEO Satellites vs. Air-to-Ground)** | Ground-Station vs. Starlink Beam Tracking Diagram, Latency Radar | 2-Min Vertical + 6-Min `16:9` |
| **07** | **How UPI Clears ₹20,000 Crore Daily in Under 2 Seconds Without Failing** | NPCI Switch Architecture, Async Queue & Retry Backoff Visualizer | 6-Min `16:9` + 2-Min Cut |
| **08** | **Why Shazam Recognizes a Song in 3 Seconds Inside a Noisy Cafe** | Live Audio Spectrogram Constellation Peak Hashing | 2-Min Vertical + 6-Min `16:9` |
| **09** | **How Noise-Canceling Headphones Invent "Anti-Sound" in Microseconds** | Phase-Inverted Sine Wave Interference Simulator | 2-Min Vertical + 6-Min `16:9` |
| **10** | **How LLMs Predict the Next Token (Transformers Visually Decoded)** | Attention Matrix Heatmap + Vector Token Space Telemetry | 6-Min `16:9` + 2-Min Cut |

---

## 4. End-to-End Weekly Automation Loop

1. **Generate Episode:** Follow `docs/QUALITY_STANDARDS.md` (Topic-First visual choice -> Dual-Voice Chatterbox + Veena generation -> Spot-check keyframe visual inspection via `read_file` -> Full `30fps` `-14 LUFS` MP4 render).
2. **Stage Upload (Private Default):**
   ```bash
   .venv/bin/python automation/youtube_bridge.py upload output/<episode>.mp4 \
     --channel decode_systems \
     --title "<CTR Title>" \
     --desc "<SEO Description + Chapters + Comment Prompt>" \
     --tags "<Comma Tags>"
   ```
3. **Publish & Telemetry Feedback Loop:**
   ```bash
   .venv/bin/python automation/youtube_bridge.py analytics --channel decode_systems --days 28
   .venv/bin/python automation/youtube_bridge.py latest --channel decode_systems
   ```
   Extract retention drop-offs, average view percentage, and viewer comments to feed Episode `N+1` script pacing and visual upgrades.
