# Behaviors — Graph Renderer

## B1: Automatic PNG on save_graph

When `save_graph()` runs, the async post-save listener:
1. Runs reader sim S1 + S2 (already implemented)
2. Runs graph health (already implemented)
3. **NEW:** Renders overlay PNG and saves to `ga_library/{slug}_overlay.png`
4. Stores overlay path in `ga_graphs.overlay_path` column

## B2: SVG Overlay on ga-detail Page

When the ga-detail page loads and a graph exists:
1. Query latest graph + latest S1 sim results
2. Render inline SVG overlay positioned on top of the GA image
3. SVG uses absolute positioning matching the GA image dimensions
4. Nodes positioned at bbox centers, scaled to image display size

## B3: Toggle Controls

Three toggles on ga-detail (below the GA image):
- **Attention** (default ON): show spheres colored by attention
- **Scanpath** (default OFF): show the reading path with timestamps
- **Problems** (default OFF): show anti-pattern markers and dead zones

Each toggle shows/hides an SVG layer group (`<g class="layer-attention">`, etc.)

## B4: Hover Interaction

Hovering a sphere node shows a tooltip:
```
[Node Name] (weight=0.85)
Attention: 72% (3 fixations, 300ms)
├─ ✓ "Main finding" (92%)
├─ ⚠ "Mechanism detail" (18%)
└─ ✗ "Safety profile" (0%)
```

## B5: Export Composite

For sharing (OG card, Telegram, PDF):
- Composite = GA image + overlay PNG merged via Pillow
- Alpha compositing: overlay at 0.7 opacity on top of GA
- Output: single PNG file

## B6: Color Interpolation

Attention ratio maps to a continuous color gradient, not discrete steps:
```
0.0  → #475569 (grey)
0.2  → #3b82f6 (blue)
0.5  → #2dd4bf (teal)
0.8  → #f59e0b (amber)
1.0  → #fbbf24 (gold)
```
Linear interpolation between anchors in RGB space.

## B7: Responsive Sizing

SVG overlay scales with the GA image. Node positions and sizes are relative (0-1 normalized), converted to pixels at render time based on display dimensions.

## B8: OG Card — Diagonal Split

The OG card (for social sharing) shows a **diagonal split**:
- Top-left triangle: original GA image (full color, no overlay)
- Bottom-right triangle: overlay render (spheres, filaments, dead zones on dark background)

The diagonal cut communicates "we reveal what's hidden" in a single glance. The split angle is ~30° from top-right to bottom-left.

Implementation: in `cards.py`, composite the GA image and the overlay PNG using a diagonal mask (Pillow polygon crop). The OG card already has the GA image — add the overlay as the second half.

## B9: Auto-play Animation on Page Load

The scanpath animation starts automatically when the page loads — no "Play" button. The user lands on the page and immediately sees the virtual eye scanning their GA. The animation runs once (5s at 1x speed), then holds the final state. A "Rejouer" button appears after completion.

## B10: Share Video Generation

A "Partager la video" button generates a 5-10s MP4 of the scanpath animation:

1. Server-side rendering using Pillow frame-by-frame (30fps = 150 frames for 5s)
2. Each frame: GA image + overlay at the corresponding tick state
   - Frame 0: all spheres grey
   - Frame 15 (0.5s): first sphere gold, eye dot moving
   - Frame 150 (5.0s): final state with all visited spheres lit
3. Frames assembled into MP4 via ffmpeg (subprocess)
4. Saved to `/var/data/videos/{slug}.mp4` (persistent disk)
5. Served at `/video/ga/{slug}.mp4`
6. Share button copies URL to clipboard + offers direct download

Fallback if ffmpeg not available: generate animated GIF instead (Pillow native, no external dep, larger file but universally supported).

The video is the viral artifact. A researcher shares it on Twitter/LinkedIn — people see an eye scanning a GA and discovering what works and what doesn't. 5 seconds of content that explains the entire value proposition.
