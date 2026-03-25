# Sync — Graph Renderer

## Current State: SPECIFIED (not implemented)

Version: 0.0 — Full doc chain complete, no code yet.

## What Exists
- `docs/GRAPH_VISUAL_STYLE.md` — Visual style guide (Pensieve aesthetic, V4)
- `docs/GRAPH_OVERLAY_MAPPING.md` — Complete data→visual mapping specification
- `docs/graph_renderer/01-10` — Full module loop documentation
- `render_graph.py` — Old renderer (networkx-based, standalone, not integrated)

## What Needs Building

### Phase 1: Core (V1)
1. `graph_renderer.py` — `assemble_render_data()`, `render_overlay_png()`, `render_overlay_svg()`
2. `_graph_overlay.html` — Jinja2 SVG template
3. DB migration: `overlay_path` column on `ga_graphs`
4. Wire into `db.py:_post_save_async()` — PNG auto-generation
5. Wire into `app.py:ga_detail()` — SVG overlay display
6. Toggle buttons on `ga_detail.html`

### Phase 2: Interaction (V2)
7. Hover tooltips on spheres
8. Scanpath playback animation (JS)
9. Animated gold particles on links (CSS keyframes)

### Phase 3: Polish (V3)
10. Pensieve textures / WebGL shader
11. Ripple animations from active spheres
12. Feed overlay back to Gemini for meta-analysis

## Dependencies
- Reader sim must have run (sim results in DB)
- Nodes must have bbox (from Gemini vision prompt V4+)
- Channel analyzer for anti-pattern data (optional, graceful degradation)

## Handoff
Next agent: implement Phase 1. Start with `graph_renderer.py`, test on immunomod graph.

## Changes Log
- 2026-03-25: Full doc chain written. Style guide V4 (Pensieve). Overlay mapping complete.
