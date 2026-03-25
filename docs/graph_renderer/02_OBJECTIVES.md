# Objectives — Graph Renderer

## Goals

1. **Render the invisible** — Show what the reader sim computed: where attention goes, what gets missed, where transmission breaks
2. **On top of the original image** — Not a separate diagram. The overlay sits directly on the GA so users see the mechanism mapped to their actual figure
3. **Every attribute = one visual** — No decoration. Each visual property encodes exactly one data dimension (see GRAPH_OVERLAY_MAPPING.md)
4. **Automatic** — Triggered by save_graph(), no manual render step
5. **Fast** — Overlay generation <2s for a typical 15-node graph

## Non-Goals

- Not a general-purpose graph renderer (only GLANCE L3 graphs)
- Not interactive 3D (flat 2D overlay)
- Not pixel-perfect to the Ideogram concept art (that's aspirational, this is functional)
- No server-side animation (scanpath playback is client-side JS)

## Trade-offs

- **SVG over Canvas** for the overlay — scalable, CSS-animatable, inspectable. Canvas only if >50 nodes (unlikely)
- **Pensieve aesthetic is aspirational** — V1 uses clean circles with glow/color, not photorealistic elemental spheres. The mapping is what matters, the rendering fidelity improves over time
- **Static PNG for sharing** (OG cards, Telegram, PDF), interactive SVG for the web page
