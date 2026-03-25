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

### 1. Full graph — blueprint overview
```
Top-down view of a scientific knowledge graph rendered as a glowing mechanism inside a dark blueprint. Deep navy background (#0a0e1a) with faint engineering grid lines. 12 metallic circular nodes of varying sizes connected by thin steel-grey links and flowing gold energy currents with animated particles. Nodes glow in a temperature spectrum: 3 nodes steaming hot red-orange, 4 nodes vibrant emerald green, 3 nodes calm blue, 2 nodes dim grey (dead). Gold energy flows along the main transmission paths like liquid light in circuits. Futuristic, intelligent, clean. No text. No labels. Ultra-detailed, 4K.
```

### 2. Overlay on GA image
```
A scientific infographic (graphical abstract) about immunology with a transparent overlay showing glowing analysis nodes. The overlay is semi-transparent dark blue. Circular metallic nodes sit on top of key visual elements — a large gold node on the main chart, medium green nodes on supporting elements, small blue nodes on minor text, grey ghost nodes on decorative elements. A dotted gold line traces the reading path from top-left to bottom-right. One area in the bottom-right has a dark red wash indicating it was never read. X-ray vision effect revealing the hidden attention mechanism. 4K, photorealistic overlay on scientific figure.
```

### 3. Gold energy flow close-up
```
Extreme close-up of a gold energy current flowing through a metallic circuit on a dark blueprint background. The current is liquid gold light — bright amber particles streaming along a curved path between two glowing nodes. Source node is large, emerald green, brushed metal surface with a bright highlight at the top edge. Target node is a hexagonal shape with a pulsing gold accent ring. The energy stream narrows at a bottleneck point where some particles turn red and fade. Volumetric lighting, cinematic, depth of field. 4K.
```

### 4. Dead zone contrast
```
Split view of a scientific graph overlay. Left side: vibrant — gold energy flowing, green and amber nodes glowing, metallic surfaces reflecting light, gold particle trails. Right side: dead zone — same graph but nodes are dim grey, no glow, a dark red translucent wash covers the area, small red X markers on unvisited nodes. The contrast between alive and dead sides of the same mechanism. Blueprint background, engineering aesthetic, cinematic lighting. 4K.
```

### 5. Reader scanpath animation frame
```
A scientific figure with an attention scanpath overlay. A glowing green entry point pulses in the top-left corner. A dotted gold line traces a Z-pattern path across the image, passing through 8 metallic nodes. Each visited node has concentric halo rings — more rings = more time spent. The largest node (center) has 3 bright gold halos. Two nodes at the bottom have no halos and are greyed out with tiny red X marks. Timestamp labels in small monospace font: "0ms", "400ms", "1200ms", "2800ms". Dark semi-transparent overlay on the scientific figure. Futuristic HUD aesthetic. 4K.
```

### 6. Anti-pattern visualization
```
Three metallic nodes on a dark blueprint background, each showing a different problem. Left node: large bright circle but with a red dashed border flickering — "fragile, single channel". Center node: medium size, border alternating between red and amber in a glitch effect — "incongruent, conflicting signals". Right node: very large circle (important) but colored cold dim blue (no attention received) — "inverse, important but invisible". Subtle warning icons float near each node. Gold energy particles approach but scatter or fade before reaching the problematic nodes. Diagnostic, clinical, precise. 4K.
```

### 7. Narrative transmission
```
A hexagonal node glowing with a bright gold pulsing ring, connected to three circular metallic carrier nodes by flowing gold energy streams. Each stream has different intensity — one thick and bright (strong transmission), one medium, one thin and fading to red (weak transmission, energy lost to friction). The hexagon represents a scientific message being carried by three visual elements. Small gold dots and red dots on the carrier nodes indicate transmission success or failure. Dark blueprint background with faint grid. The gold light from the successful streams illuminates the surrounding area. Cinematic, volumetric. 4K.
```

### 8. Full dashboard view
```
A futuristic scientific analysis dashboard showing a graphical abstract in the center with a glowing graph overlay. Left panel: aggregate stats in monospace font — "Clarity: 72% CLAIR", "Coverage: 14/17", "Narratives: 3/4". Right panel: vertical list of recommendations with amber warning icons. The graph overlay on the central image shows the full mechanism — gold flows, temperature-coded nodes, scanpath trail, dead zone wash in the bottom corner. Blueprint aesthetic, dark theme, clean typography, professional. Widescreen 16:9, 4K.
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
