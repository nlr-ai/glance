# GLANCE Graph Visual Style — Pensieve

## Concept

The graph is a **pensieve** — a vessel where thoughts become visible, tangible matter. The viewer looks down into a shallow pool of dark luminous liquid where **materialized thoughts** float as glowing elemental spheres, connected by shimmering filaments of meaning.

Half forge (raw energy, heat, materiality), half circuit (precision, flow, structure). Not too virtual, not too real. The aesthetic of **ideas that have weight** — thoughts you can see and touch, suspended in a medium that reveals their connections.

Each sphere is a concept from the scientific figure. The liquid carries energy between them. Where understanding flows freely, gold filaments shimmer. Where comprehension breaks, the liquid darkens and the spheres dim.

---

## Palette

### Background — The Pensieve Basin
- **Dark luminous liquid**: `#0a0e1a` → `#0f172a`, with subtle swirling currents visible on the surface
- The liquid has depth — faint reflections and refractions from the glowing spheres below
- Surface texture: smooth but alive — micro-ripples radiate outward from active spheres
- Slight silvery sheen on the liquid surface (`rgba(148,163,184,0.05)`)
- Edges of the basin are dark, center is brighter (lit by the spheres within)

### Nodes — Elemental Thought Spheres

Each node is a **materialized thought** — a glowing sphere of elemental energy suspended in the liquid. The sphere type reflects its energy state:

| State | Sphere | Hex | Glow | Meaning |
|-------|--------|-----|------|---------|
| Hot (high tension) | Molten fire sphere, surface cracking with light | `#ff6b35` → `#ff3d1f` | Intense bloom, 20px, heat distortion | Unresolved, demands attention |
| Warm (active) | Amber plasma sphere, swirling internal light | `#f59e0b` → `#fbbf24` | Medium bloom, 12px | Active processing, energy flowing |
| Resolved (transmitted) | Emerald crystal sphere, steady inner glow | `#10b981` → `#34d399` | Steady glow, 8px | Message successfully transmitted |
| Cool (stable) | Blue ice sphere, calm frozen luminescence | `#3b82f6` → `#60a5fa` | Soft glow, 6px | Stable, low urgency |
| Dead (skipped) | Dark stone sphere, no light, sinking | `#475569` → `#64748b` | None | Never reached, thought lost |

Sphere surface: each has visible **internal structure** — not solid, not hollow. Like looking into a marble made of light. Larger spheres (higher weight) have more complex internal patterns.

### Node Shapes by Type

| Type | Shape | Size | Surface |
|------|-------|------|---------|
| **space** | Rounded rectangle, dashed border | Large (contains children) | Translucent dark panel (`rgba(15,23,42,0.6)`), border matches energy color |
| **thing** | Circle or rounded square | Proportional to weight (min 24px, max 64px) | Solid metallic, energy-colored, inner shadow |
| **narrative** | Hexagon or diamond | Medium fixed (40px) | Brighter glow, pulsing animation (0.5Hz), gold accent ring |

### Links — Shimmering Filaments

Links are **luminous filaments** in the liquid — like threads of memory connecting thoughts in the pensieve. Silvery-gold, translucent, alive.

| Link Type | Style | Color | Animation |
|-----------|-------|-------|-----------|
| **thing → narrative** (carries message) | Thick golden filament, bright current | `#f59e0b` → `#fbbf24` | Bright particles stream along filament, liquid ripples along the path |
| **thing → space** (containment) | Thin silver thread | `#94a3b8` (silver) | Static, faint, 1px |
| **thing → thing** (visual relation) | Medium silver filament | `#64748b` | Static, 1.5px |
| **narrative → space** (residency) | Gossamer thread, barely visible | `#334155` | Static, 0.5px |

Filament width scales with weight: `width = 1 + weight * 3` (px).

High-weight filaments (≥ 0.8): the gold intensifies, the liquid around the filament glows, ripples expand outward.

### Gold Energy Flow — The Star Visual

The **gold filaments** are the hero. Energy flows through the liquid between spheres — visible as bright particles streaming along the filament paths, leaving trails of light in the dark liquid.

- Filament color: warm gold `#f59e0b` → `#fbbf24` → `#fcd34d`
- Particles: bright dots (3px) streaming along filaments, speed = link_weight
- The liquid AROUND active filaments glows faintly gold (subsurface illumination)
- Convergence points: where 3+ filaments meet, the liquid brightens to `#fff7ed` (white-gold pool)
- Penalty visualization: on anti-pattern links, the filament dims, particles slow and dissolve into the liquid before reaching the target
- Dead links: filament is dark, no particles, the liquid is still and opaque along this path

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

## Ideogram Prompts (V4 — Elemental Pensieve)

All prompts: **flat top-down view** looking down into a dark luminous basin. Elemental energy spheres connected by shimmering filaments.

### 1. Full graph
```
Flat top-down view looking into a shallow dark basin filled with luminous black liquid. 12 elemental energy spheres of different sizes float in the liquid — 3 are molten fire spheres with cracking orange-red surfaces radiating heat, 4 are emerald crystal spheres with steady green inner glow, 3 are blue ice spheres with calm frozen luminescence, 2 are dark stone spheres sinking with no light. Shimmering gold filaments connect the spheres through the liquid, carrying bright particles that stream between them. Where filaments converge the liquid glows white-gold. The liquid surface shows micro-ripples radiating from active spheres. Each sphere has visible internal structure like a marble made of light. Dark, luminous, elemental. No text. 16:9, 4K.
```

### 2. Overlay on GA image
```
Flat top-down view of a scientific infographic with a dark translucent liquid overlay. Elemental spheres float above key visual elements — a large golden plasma sphere on the main chart, medium emerald spheres on supporting elements, small blue ice spheres on minor text, dark stone spheres on decorations. Shimmering gold filaments connect the spheres through the overlay. Bottom-right area: liquid darkens to opaque, spheres are dark, no filaments — dead zone. The scientific figure is visible through the liquid like looking through dark water. 4K.
```

### 3. Gold filament close-up
```
Flat top-down extreme close-up of a shimmering gold filament connecting two elemental spheres through dark luminous liquid. The filament carries bright amber particles streaming between the spheres — particles leave trails of light in the liquid. Source sphere: large emerald crystal with swirling green internal light. Target sphere: smaller, hexagonal facets, gold-rimmed. The filament narrows at a point where particles dim and dissolve into the liquid — energy lost. The dark liquid around the filament glows faintly gold from subsurface illumination. Macro, cinematic. 4K.
```

### 4. Dead zone contrast
```
Flat top-down view of a dark basin split in two. Left half: alive — fire and emerald spheres glow intensely, gold filaments shimmer with streaming particles, the liquid ripples and reflects warm light, white-gold pools at convergence points. Right half: dead — same basin but spheres are dark stone, no glow, the liquid is still and opaque black, filaments are dark threads with no particles, faint red glow from dying embers inside the stone spheres. Sharp boundary between life and death. 4K.
```

### 5. Reader scanpath
```
Flat top-down view of elemental spheres in dark liquid with a diagnostic path overlay. A bright green sphere pulses at top-left — entry point. A dotted gold filament traces a Z-pattern through 8 spheres. Each visited sphere has concentric ripple rings in the liquid — more rings = longer attention. Center sphere: 3 bright gold ripple halos. Two bottom spheres: dark stone, no ripples, faint red warning glow. Tiny monospace timestamps float on the liquid surface: "0ms", "400ms", "1200ms". Dark luminous basin, HUD aesthetic. 4K.
```

### 6. Anti-pattern faults
```
Flat top-down view of three elemental spheres in dark liquid, each showing a fault. Left: large fire sphere with only one thin fragile filament connection — the filament flickers, about to break. Center: medium sphere with surface flickering between orange and green — conflicting elemental energies fighting inside. Right: very large sphere but cold dark blue, almost stone — important but receiving no energy from any filament. Gold particles approach but scatter into the liquid before reaching the faulty spheres. Diagnostic, precise. 4K.
```

### 7. Narrative transmission
```
Flat top-down view of a large hexagonal sphere with bright gold pulsing ring, connected to three smaller spheres by gold filaments of different intensities through dark liquid. Thickest filament: dense particle stream, liquid glows gold around it — strong transmission. Medium filament: moderate flow. Thinnest filament: particles fading to red, dissolving into dark liquid — weak transmission. Small gold and red indicator lights on each carrier sphere. The liquid around the main filaments shimmers. Cinematic glow. 4K.
```

### 8. Full dashboard
```
Flat top-down view of a futuristic analysis screen. Center: a scientific figure with elemental sphere overlay — gold filament flows, temperature-coded spheres, ripple scanpath, dark dead zone. Left panel: diagnostic readout in monospace on dark glass — "Clarity: 72%", "Coverage: 14/17", "Narratives: 3/4". Right panel: fault list with amber warning glyphs. The pensieve aesthetic — dark liquid, glowing spheres, shimmering filaments — contained in a clinical diagnostic frame. Widescreen 16:9. 4K.
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
