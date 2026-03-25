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

## Implementation Notes

- Use `render_graph.py` as the rendering engine
- SVG preferred for web (scalable, animatable)
- Canvas fallback for performance on large graphs (>30 nodes)
- Gold particle animation: CSS `@keyframes` on SVG `<circle>` elements along `<path>` with `offset-path`
- Metallic sheen: SVG `<linearGradient>` with white-to-transparent top band
- Glow: SVG `<filter>` with `feGaussianBlur` + `feComposite`
- Blueprint grid: SVG `<pattern>` tiled across background
