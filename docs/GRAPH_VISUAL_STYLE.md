# GLANCE Graph Visual Style — Blueprint Mechanism

## Concept

The graph is a **secret mechanism inside a machine**. The viewer is looking at the internal workings of a scientific figure — gears, circuits, energy flows that are normally invisible. The graph reveals *how information actually moves* through the visual.

Not a diagram. Not a chart. A **living blueprint** of attention and meaning.

---

## Palette

### Background
- **Deep blueprint**: `#0a0e1a` base, with subtle grid lines (`#141c2e`, 0.5px, 40px spacing)
- Grid style: engineering blueprint — faint orthogonal lines, no labels
- Slight radial gradient from center (lighter) to edges (darker) — the mechanism is illuminated from within
- Optional: faint schematic annotations at edges (measurement marks, zone boundaries) in `#1a2540`

### Nodes — Temperature-Coded Energy

Nodes glow based on their **energy state** (how much attention they receive or how much tension they hold):

| State | Color | Hex | Glow | Meaning |
|-------|-------|-----|------|---------|
| Hot (high energy/tension) | Steaming red-orange | `#ff3d1f` → `#ff6b35` | Intense bloom, 20px | Unresolved, demands attention |
| Warm (active) | Molten amber | `#f59e0b` → `#fbbf24` | Medium bloom, 12px | Active processing |
| Neutral (resolved) | Vibrating green | `#10b981` → `#34d399` | Steady glow, 8px | Message transmitted |
| Cool (stable/background) | Calm blue | `#3b82f6` → `#60a5fa` | Soft glow, 6px | Stable, low urgency |
| Dead (orphan/skipped) | Dim grey | `#475569` → `#64748b` | No glow | Never reached |

Node surface: **metallic sheen** — subtle linear gradient top-to-bottom simulating brushed metal. Reflection highlight at top edge (2px lighter band).

### Node Shapes by Type

| Type | Shape | Size | Surface |
|------|-------|------|---------|
| **space** | Rounded rectangle, dashed border | Large (contains children) | Translucent dark panel (`rgba(15,23,42,0.6)`), border matches energy color |
| **thing** | Circle or rounded square | Proportional to weight (min 24px, max 64px) | Solid metallic, energy-colored, inner shadow |
| **narrative** | Hexagon or diamond | Medium fixed (40px) | Brighter glow, pulsing animation (0.5Hz), gold accent ring |

### Links — Energy Currents

| Link Type | Style | Color | Animation |
|-----------|-------|-------|-----------|
| **thing → narrative** (carries message) | Flowing gold current | `#f59e0b` → `#fbbf24` | Animated particles flowing source→target, speed = link weight |
| **thing → space** (containment) | Thin metallic connector | `#475569` (grey steel) | Static, 1px, dashed |
| **thing → thing** (visual relation) | Medium metallic | `#64748b` (silver) | Static, 1.5px, solid |
| **narrative → space** (residency) | Faint guide line | `#334155` (dark steel) | Static, 0.5px, dotted |

Link thickness scales with weight: `width = 1 + weight * 3` (px).

High-weight links (≥ 0.8): add subtle glow matching the source node color.

### Gold Energy Flow

The **gold current** is the star visual. It represents attention/energy flowing from things to narratives — the transmission of meaning.

- Color: warm gold gradient `#f59e0b` → `#fbbf24` → `#fcd34d`
- Animated particles: small circles (3px) traveling along link paths
- Particle speed proportional to `link_weight` (fast = strong transmission)
- Particle density proportional to `fixation_strength` from reader sim
- Trail: fading afterglow behind particles (opacity decay over 100ms)
- On links with anti-pattern penalties: particles turn red, slow down, some disappear mid-path (visualizes transmission loss)

---

## Node Labels

- Font: monospace (`SF Mono`, `Fira Code`, fallback `Consolas`)
- Size: 10px for things, 11px for narratives, 9px for spaces
- Color: `#cbd5e1` (light steel)
- Position: below node, centered
- Truncate at 25 chars + `...`
- Weight shown as small badge: `w=0.85` in `#64748b`, 8px, top-right of node

---

## Reader Simulation Overlay

When displaying the reader sim scanpath on the graph:

- **Scanpath line**: dotted gold line connecting visited nodes in order, with timestamp labels
- **Entry point**: pulsing green circle at first node (the eye enters here)
- **Fixation halos**: concentric rings around each visited node, size = time spent (ms)
- **Dead zones**: spaces/nodes never visited get a dark overlay (`rgba(0,0,0,0.5)`) with a red "X" watermark
- **Attention flow**: gold particle animation follows the scanpath in real-time (playable, 5s = 5s or accelerated)

---

## Anti-Pattern Indicators

| Anti-pattern | Visual |
|-------------|--------|
| **fragile** | Single thin link glows red, warning icon (⚠) on node |
| **incongruent** | Node border flickers between two colors (the conflicting channels) |
| **inverse** | Node size large (high weight) but dim glow (low channel effectiveness) — visual contradiction |
| **orphan** | Node faded to ghost opacity (0.3), no glow, grey border |

---

## Layout

- Force-directed base layout (d3-force or similar)
- Spaces as containers: their children cluster inside
- Z-order matches reading order (top-left = first visited)
- When bbox data is available: nodes positioned at their real image coordinates
- Minimum spacing: 60px between nodes to prevent overlap

---

## Rendering Targets

| Target | Format | Resolution |
|--------|--------|------------|
| ga-detail page | Interactive SVG/Canvas | Responsive |
| Admin dashboard | Static SVG thumbnail | 400x300 |
| PDF export | Static SVG | 1200x900 |
| OG card overlay | Simplified (nodes only, no labels) | 600x315 |
| Telegram bot | Static PNG | 800x600 |

---

## CSS Variables (for web rendering)

```css
:root {
    --graph-bg: #0a0e1a;
    --graph-grid: #141c2e;
    --graph-grid-accent: #1a2540;

    --node-hot: #ff3d1f;
    --node-warm: #f59e0b;
    --node-green: #10b981;
    --node-cool: #3b82f6;
    --node-dead: #475569;
    --node-metal-highlight: rgba(255,255,255,0.12);

    --link-gold: #f59e0b;
    --link-gold-light: #fcd34d;
    --link-steel: #475569;
    --link-silver: #64748b;
    --link-faint: #334155;

    --label-color: #cbd5e1;
    --label-dim: #64748b;

    --glow-hot: 0 0 20px rgba(255,61,31,0.6);
    --glow-warm: 0 0 12px rgba(245,158,11,0.5);
    --glow-green: 0 0 8px rgba(16,185,129,0.4);
    --glow-cool: 0 0 6px rgba(59,130,246,0.3);
}
```

---

## Ideogram Test Prompts

All prompts use **top-down flat view** — looking straight down at the mechanism, like a blueprint on a table. No perspective, no 3D angle.

### 1. Full graph — blueprint overview
```
Flat top-down view looking straight down at a scientific knowledge graph rendered as a glowing mechanism on a dark blueprint table. Deep navy background with faint engineering grid lines. 12 metallic circular nodes of varying sizes connected by thin steel-grey links and flowing gold energy currents. Nodes glow in a temperature spectrum: 3 nodes steaming hot red-orange, 4 nodes vibrant emerald green, 3 nodes calm blue, 2 nodes dim grey dead. Gold energy flows along the main paths like liquid light in circuits. Flat 2D layout, no perspective, no 3D. Futuristic, intelligent, clean. No text. Ultra-detailed, 4K.
```

### 2. Overlay on GA image
```
Flat top-down view of a scientific infographic about immunology with a transparent glowing overlay. Seen from directly above. Semi-transparent dark blue layer over the figure. Circular metallic nodes positioned on key elements — a large gold node on the main chart, medium green nodes on supporting elements, small blue nodes on minor text, grey ghost nodes on decorations. A dotted gold line traces the reading path in Z-pattern. Bottom-right area has a dark red wash — never read. Flat 2D, no perspective. X-ray vision effect. 4K.
```

### 3. Gold energy flow close-up
```
Flat top-down close-up of a gold energy current flowing through a metallic circuit on a dark blueprint surface. The current is liquid gold light — bright amber particles streaming along a curved path between two glowing nodes. Source node: large, emerald green, brushed metal. Target node: hexagonal with gold accent ring. The stream narrows at a bottleneck where particles turn red and fade. Flat 2D view from above, no perspective. Volumetric glow, cinematic lighting. 4K.
```

### 4. Dead zone contrast
```
Flat top-down split view of a scientific graph. Left half: vibrant — gold energy flowing, green and amber nodes glowing, metallic surfaces, gold particle trails. Right half: dead zone — nodes dim grey, no glow, dark red translucent wash, small red X markers. Sharp contrast between alive and dead sides. Flat 2D blueprint, seen from directly above. Engineering aesthetic. 4K.
```

### 5. Reader scanpath
```
Flat top-down view of a scientific figure with an attention scanpath overlay. Glowing green entry point top-left. A dotted gold line traces a Z-pattern through 8 metallic nodes. Each visited node has concentric halo rings — more rings = more time spent. Center node has 3 bright gold halos. Two bottom nodes greyed out with red X marks. Small monospace timestamps: "0ms", "400ms", "1200ms". Flat 2D HUD overlay, no perspective. Futuristic. 4K.
```

### 6. Anti-pattern visualization
```
Flat top-down view of three metallic nodes on a dark blueprint surface. Left: large bright circle with red dashed border — fragile, single channel. Center: medium node with border alternating red and amber — incongruent, conflicting signals. Right: very large circle colored cold dim blue — inverse, important but invisible. Gold energy particles approach but scatter before reaching them. Flat 2D, no perspective. Diagnostic, precise. 4K.
```

### 7. Narrative transmission
```
Flat top-down view of a hexagonal node with bright gold pulsing ring, connected to three circular metallic nodes by flowing gold energy streams. One stream thick and bright — strong transmission. One medium. One thin, fading to red — weak, energy lost. Small gold and red dots on carrier nodes. Dark blueprint surface with faint grid. Gold light illuminates surrounding area. Flat 2D, no perspective. Cinematic glow. 4K.
```

### 8. Full dashboard view
```
Flat top-down view of a futuristic scientific analysis dashboard. Center: a graphical abstract with glowing graph overlay — gold flows, temperature-coded nodes, scanpath trail, dead zone wash. Left panel: stats in monospace — "Clarity: 72%", "Coverage: 14/17", "Narratives: 3/4". Right panel: recommendations with amber warning icons. Dark blueprint theme, clean typography. Flat 2D layout, no perspective. Widescreen 16:9. 4K.
```

---

## Implementation Notes

- Use `render_graph.py` as the rendering engine
- SVG preferred for web (scalable, animatable)
- Canvas fallback for performance on large graphs (>30 nodes)
- Gold particle animation: CSS `@keyframes` on SVG `<circle>` elements along `<path>` with `offset-path`
- Metallic sheen: SVG `<linearGradient>` with white-to-transparent top band
- Glow: SVG `<filter>` with `feGaussianBlur` + `feComposite`
- Blueprint grid: SVG `<pattern>` tiled across background
