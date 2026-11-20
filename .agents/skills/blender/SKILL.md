---
name: blender
description: >-
  Studio runbook and quality workflow for Blender 5.3+ 3D scenes in eternal-ai-studio,
  covering Topic-First suitability checks, the official Blender Lab MCP Server (`lab_blender_org/mcp`),
  iterative live viewport verification, and Apple M2 (8 GB RAM) headless EEVEE rendering rules.
  Use ONLY AFTER analysing the video topic confirms that 3D spatial anatomy or physical environments
  genuinely serve the explainer better than 2D Canvas motion graphics or real screen recordings.
---

# Eternal AI Studio — Blender 5.3 & Official Blender Lab MCP Workflow

## 0. Topic-Fit Gate (Analyse Before Using This Skill!)

**Do NOT default to Blender for every video.** First analyse the topic:
- **Use Blender 3D when:** The story relies on physical world realism, spatial camera movement through hardware/architecture, or tangible physical scale (`@fewshot.studio` style).
- **Skip Blender 3D when:** Explaining software/browser workflows (`Google Colab`, `UDISE+`), maps, timelines, or algorithms best taught with **bespoke per-beat Canvas/SVG motion diagrams** or **authentic zoomed screen captures**.
- **Anti-Repetition Rule:** Never render 4–5 small 3D loops and repeat them across dozens of unrelated beats (`google_colab_masterclass_16x9.mp4` lesson). Every 3D shot must directly illustrate the exact sentence being spoken.

---

This skill governs all approved 3D scene work in `eternal-ai-studio` on **Blender 5.3.0** (`/opt/homebrew/bin/blender`, add-on `lab_blender_org/mcp v1.0.3`), using [blender_studio_kit.py](file:///Volumes/Eternal%20T7/PROJECT/eternal-ai-studio/engine/blender_studio_kit.py) and the official [blender_mcp](file:///Volumes/Eternal%20T7/PROJECT/blender_mcp) server.

## 1. Live MCP Server Architecture (Already Installed & Wired)

```text
Antigravity Client  ⇐ stdio ⇒  /Volumes/Eternal T7/PROJECT/blender_mcp/mcp/.venv/bin/blender-mcp  ⇐ TCP localhost:9876 ⇒  Blender 5.3 Add-on (lab_blender_org/mcp)
```

- **Global MCP Config:** `/Users/eternalstudent/.gemini/config/mcp_config.json` (`blender` server with `BLENDER_PATH=/opt/homebrew/bin/blender`, `BLENDER_MCP_HOST=localhost`, `BLENDER_MCP_PORT=9876`). Restarting/reloading the Antigravity session exposes all official MCP tools directly; within this terminal session you can also invoke `blmcp.tools_helpers.connection.send_code(...)` using `/Volumes/Eternal T7/PROJECT/blender_mcp/mcp/.venv/bin/python` while Blender is running.
- **Blender Add-on Location:** `~/Library/Application Support/Blender/5.3/extensions/lab_blender_org/mcp/` (`use_autostart=True` on `localhost:9876`; requires **Allow Online Access** enabled in Blender **Settings → System → Network**).
- **Safe CLI Fallback:** When Blender GUI is closed or rendering full sequences reproducibly from code:
  ```bash
  blender -b --factory-startup --python scenes/<scene_name>.py -- --spot-only
  ```

## 2. Iterative Build Loop (No More Blind 25-Min Renders)

Always build and verify scenes **interactively** before committing to batch frame output:

1. **Inspect First (`get_objects_summary`, `get_blendfile_summary_datablocks`, `get_screenshot_of_window_as_json`):** Verify units, active render engine (`BLENDER_EEVEE`), lighting, and collection layout.
2. **Focus & Visually Audit Every Shot (`jump_to_view3d_object_by_name`, `get_screenshot_of_area_as_image`, `render_thumbnail_to_path`):** Inspect viewport/thumbnail images directly via `read_file` to verify camera framing, silhouette separation, non-clipping props, and material contrast *while the scene is cheap to tweak*.
3. **API Grounding (`search_api_docs`, `get_python_api_docs`, `search_manual_docs`):** Look up exact Blender 5.3 `bpy` signatures instead of guessing node socket names or layered action APIs.
4. **Bake Into Clean Versioned Script:** Export finalized procedural/layout code into `scenes/<scene_name>.py` calling [blender_studio_kit.py](file:///Volumes/Eternal%20T7/PROJECT/eternal-ai-studio/engine/blender_studio_kit.py) and test `--spot-only` boundary cuts (`f_next_cut - 1` vs `f_next_cut`) before full render.

## 3. Hard Studio Visual Rules (Learned From Past Rejections)

1. **Zero Visual Style Clash:** Never mix rough 2D stick figures inside lit 3D Blender worlds (`Episode 01` failed for this). Use Blender **only** for cohesive 3D hero metaphors/shots (e.g., 2–5 second physical storytelling openers), or clean dark-studio 3D objects—paired with crisp floating glass HUD callouts (`compositor/hybrid_overlay.py`), never low-effort primitives in an empty black void (`POC #1`).
2. **Respect Apple M2 (8 GB Unified RAM) EEVEE Limits:**
   - Use `setup_world(..., samples=16)` (`taa_render_samples = 16`, `use_raytracing = False`, `AgX - Medium High Contrast`, `use_persistent_data = False`).
   - Use `iter_action_fcurves(action)` for Blender 5.x layered/slotted actions.
   - Avoid semi-transparent EEVEE refractive glass (`transmission`) which sparkles at 16 samples; use opaque/metallic rim shaders + bloom or 2D HTML glass HUD overlays instead.
3. **Never Run Unbacked Destructive Edits via Live MCP:** Save `.blend` milestones inside `build/` before running major geometry/material rewrites over `execute_blender_code`.
