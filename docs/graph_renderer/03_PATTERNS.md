# Patterns — Graph Renderer

## P1: Data-Driven, Not Decorative

Every visual property maps to exactly one data dimension. No ornamental elements.

| Visual | Data | Source |
|--------|------|--------|
| Position | bbox center | Gemini vision |
| Size | weight | Graph node |
| Fill color | attention received | Reader sim |
| Border | anti-pattern | Channel analyzer |
| Glow radius | energy (tension) | Graph node |
| Opacity | stability | Graph node |
| Narrative badges | narrative reached/missed | Reader sim |
| Space outlines | dead/visited | Reader sim |
| Link width | relationship weight | Graph link |
| Gold particles | transmission strength | Reader sim + link weight |

Reference: `docs/GRAPH_OVERLAY_MAPPING.md`

## P2: Layer Stack

Bottom to top:
1. GA Image (original)
2. Dim overlay (darken so spheres pop)
3. Space outlines (bbox containers)
4. Links/filaments
5. Thing spheres (positioned at bbox centers)
6. Narrative badges (edge indicators on spheres)
7. Scanpath trail (optional, toggleable)
8. Problem markers (optional, toggleable)

## P3: Two Render Targets

| Target | Format | Engine | When |
|--------|--------|--------|------|
| Web (ga-detail) | SVG overlay on `<img>` | Jinja2 template → inline SVG | Page load |
| Export (share, OG, TG, PDF) | PNG composite | Pillow (PIL) | save_graph async |

Both render from the same data. The SVG template and the PIL renderer read the same graph + sim results.

## P4: Progressive Enhancement

V1 ships with:
- Circles with color fill + glow (CSS box-shadow)
- Straight lines for links
- Color coding from the mapping

V2 adds:
- Animated gold particles on links (CSS keyframes)
- Scanpath playback
- Hover tooltips

V3 (aspirational):
- Pensieve textures (WebGL shader or pre-rendered sprite)
- Ripple animations
- Depth-of-field blur at edges

## P5: No External Dependencies for V1

The PNG renderer uses only Pillow (already in requirements).
The SVG renderer uses only Jinja2 (already in requirements).
No D3, no Canvas libraries, no WebGL for V1.
