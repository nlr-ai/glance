# Live Scanpath — Real-time Reading Simulation Animation

## Concept

The user clicks "Play" and watches a virtual eye scan their GA in real-time. 5 seconds = 5 seconds. Spheres light up one by one as the eye reaches them. Gold energy flows along filaments as attention transmits to narratives. Dead zones stay dark. The user FEELS what a reader experiences.

This is the hero moment of GLANCE. Not a score. Not a report. A lived experience.

---

## UX Flow

1. User is on `/analyze?ga=slug` or `/ga-detail/slug`
2. GA image displayed with transparent overlay (spheres positioned but all grey/dim)
3. User clicks **"Simuler la lecture"** button
4. **5-second animation begins:**
   - t=0ms: Entry point (top-left) pulses green. First sphere lights up gold.
   - t=100ms: Each tick, the "eye" moves to the next sphere in Z-order
   - Sphere transitions: grey → blue → teal → amber → gold (proportional to fixation time)
   - Gold filaments light up as attention flows to narratives
   - Narrative badges (gold dots) appear when a narrative is reached
   - Dead zones stay dark — the absence IS the message
5. After 5s: final state holds. Stats appear: "14/17 elements lus — 3 messages transmis sur 4"
6. Button changes to **"Rejouer"**

Optional: speed control (1x = 5s real-time, 2x = 2.5s, 5x = 1s)

---

## Architecture

### No WebSocket needed

The reader sim runs in <1ms. We don't need server-sent events. We pre-compute the full scanpath on page load and animate client-side with JavaScript `requestAnimationFrame`.

```
Page load → fetch /analyze/tool/reader_sim/{slug} → get full scanpath
         → build animation timeline from scanpath data
         → user clicks Play → JS animates through timeline
```

### Data Structure (from reader_sim result)

The scanpath already has everything we need:

```json
{
  "scanpath": [
    {"tick": 0, "time_ms": 0, "node_id": "thing:title", "x": 0.15, "y": 0.05, "attention": 1.0, "fixation": 0.85},
    {"tick": 1, "time_ms": 100, "node_id": "thing:title", "x": 0.15, "y": 0.05, "attention": 1.0, "fixation": 0.85},
    {"tick": 3, "time_ms": 300, "node_id": "thing:chart", "x": 0.5, "y": 0.4, "attention": 0.95, "fixation": 0.76},
    ...
  ],
  "plan_vs_actual": [...],
  "heatmap": [...],
  "narrative_details": [
    {"id": "narrative:main", "name": "...", "received": 0.92, "status": "reached"},
    ...
  ],
  "dead_spaces": [...],
  "skipped_nodes": [...],
  "recommendations": [...]
}
```

### Animation Timeline

Convert scanpath ticks to animation keyframes:

```javascript
const TICK_MS = 100;  // 100ms per tick in sim
const SPEED = 1.0;    // 1x = real-time

// Pre-process: group consecutive ticks on same node
// [{node_id, start_ms, end_ms, total_fixation, x, y}]
const timeline = buildTimeline(scanpath);

// Animation loop
let startTime = null;
function animate(timestamp) {
    if (!startTime) startTime = timestamp;
    const elapsed = (timestamp - startTime) * SPEED;

    // Find which node is being fixated at this time
    const currentStep = timeline.find(s => s.start_ms <= elapsed && elapsed < s.end_ms);

    // Update all nodes
    for (const node of allNodes) {
        const nodeTimeline = timeline.filter(t => t.node_id === node.id);
        const visited = nodeTimeline.some(t => t.start_ms <= elapsed);
        const isActive = currentStep && currentStep.node_id === node.id;

        if (isActive) {
            // Currently being fixated — bright, pulsing
            node.el.style.fill = attentionToColor(node.cumulativeAttention);
            node.el.style.filter = `drop-shadow(0 0 20px ${attentionToColor(node.cumulativeAttention)})`;
            node.el.style.transform = 'scale(1.15)';
        } else if (visited) {
            // Previously visited — steady glow
            node.el.style.fill = attentionToColor(node.cumulativeAttention);
            node.el.style.filter = `drop-shadow(0 0 8px ${attentionToColor(node.cumulativeAttention)})`;
            node.el.style.transform = 'scale(1)';
        } else {
            // Not yet visited — dim grey
            node.el.style.fill = '#475569';
            node.el.style.filter = 'none';
            node.el.style.opacity = '0.4';
        }
    }

    // Update eye position (scanning dot)
    if (currentStep) {
        eyeDot.style.cx = currentStep.x;
        eyeDot.style.cy = currentStep.y;
        eyeDot.style.display = '';
    }

    // Update scanpath trail (gold dotted line)
    const visitedPoints = timeline
        .filter(t => t.start_ms <= elapsed)
        .map(t => `${t.x},${t.y}`);
    scanpathLine.setAttribute('points', visitedPoints.join(' '));

    // Update narrative badges (appear when reached)
    // Update filaments (light up when both endpoints visited)
    // Update progress bar

    if (elapsed < totalDuration) {
        requestAnimationFrame(animate);
    } else {
        showFinalStats();
    }
}
```

### Visual Elements During Animation

| Element | Before animation | During fixation | After fixation | Never reached |
|---------|-----------------|----------------|---------------|---------------|
| **Sphere** | Grey, dim, opacity 0.4 | Bright color, scale 1.15, intense glow, pulse | Steady color, scale 1.0, soft glow | Stays grey |
| **Eye dot** | Hidden | Bright white dot (6px) at current position | N/A | N/A |
| **Scanpath trail** | Hidden | Gold dotted line grows as eye moves | Full line visible | N/A |
| **Filament** | Dark grey | N/A | Lights up gold when both endpoints visited | Stays dark |
| **Narrative badge** | Hidden | N/A | Gold dot appears when narrative reached | Red dot at end |
| **Space outline** | Faint grey | Teal when eye enters | Teal (visited) | Red dashed (dead) |
| **Progress bar** | 0% | Grows proportionally | 100% | N/A |
| **Timer** | "0.0s" | Counts up in real-time | "5.0s" | N/A |

### Saccade Animation

When the eye jumps between nodes (saccade):
- Eye dot moves along a smooth bezier curve (not teleport)
- Duration: 150ms per saccade (fast but visible)
- A faint gold trail follows the eye during the jump
- The trail fades after 300ms

### Sound Design (V2, optional)

- Soft "ping" when a sphere lights up (pitch proportional to weight)
- Low hum during fixation (volume proportional to attention)
- Warning tone when entering a dead zone
- Completion chime at 5s

---

## Implementation Plan

### Phase 1: Static → Animated

1. The overlay SVG already has all spheres positioned (from graph_renderer)
2. Add animation JS that reads the scanpath data
3. On click "Play": animate through the scanpath in real-time
4. Show progress bar + timer

### Phase 2: Enhanced

5. Saccade bezier animations for eye movement
6. Filament progressive lighting
7. Narrative badge pop-in
8. Speed control (0.5x, 1x, 2x, 5x)

### Phase 3: Interactive

9. Click on any tick point to jump to that moment
10. Hover shows "at this moment, the reader was looking at X"
11. Side-by-side: System 1 (5s) vs System 2 (90s) animation

---

## Data Flow

```
/analyze?ga=slug (page load)
    │
    ├─ GET /ga/{filename} → GA image
    │
    ├─ graph + sim already in DB (from save_graph auto-trigger)
    │
    ├─ render_overlay_svg(graph, sim) → SVG with all spheres (grey)
    │
    └─ sim.scanpath → embedded as JSON in page
                │
                └─ User clicks "Play"
                        │
                        └─ JS requestAnimationFrame loop
                            ├─ Updates sphere colors/glow
                            ├─ Moves eye dot
                            ├─ Extends scanpath trail
                            ├─ Lights filaments
                            └─ Shows badges + stats at end
```

No server calls during animation. Everything client-side.

---

## Hover: Node Detail Card

When the user hovers a sphere (during or after animation), a floating card appears next to the sphere:

```
┌──────────────────────────────────────┐
│  OM-85 (w=1.00)                      │
│  Attention: 300ms — 13% du total     │
│  ────────────────────────────────     │
│  Messages portés:                    │
│  ✓ Fracture du Cycle (92%)           │
│  ⚠ Hiérarchie d'Évidence (18%)       │
│  ✗ Axe Intestin-Poumon (0%)          │
│  ────────────────────────────────     │
│  Canaux: color_hue (0.95),           │
│          size (0.80), position (0.70) │
│  Anti-pattern: aucun                 │
└──────────────────────────────────────┘
```

Data sources for the card:
- `name`, `weight` → graph node
- Attention ms, % → reader sim heatmap
- Messages portés → linked narratives + sim narrative_attention
- Canaux → visual_channels from enriched graph (if available)
- Anti-pattern → graph metadata anti_patterns

The card follows the cursor but stays within viewport bounds.
During animation: card shows "En cours de lecture..." until the sphere is reached, then shows real data.

## Hover: Space Zone

Hovering a space outline shows:
```
┌──────────────────────────────────┐
│  Zone: Header (gauche)           │
│  4 éléments — 3 lus, 1 raté     │
│  Message: "Résultat principal"   │
│  Statut: ✓ transmis (85%)       │
└──────────────────────────────────┘
```

## Post-Animation: Reading Interpretation

After the 5s animation completes, a **reading interpretation panel** slides in below the overlay:

```
┌─────────────────────────────────────────────────────┐
│  LECTURE SIMULÉE — 5.0s                             │
│                                                     │
│  Le lecteur entre par 'OM-85' dans le header,       │
│  qui reçoit 300ms d'attention. Il parcourt ensuite  │
│  la zone centrale (Épithélium, Lamina Propria)      │
│  mais n'atteint jamais les conclusions en bas.       │
│                                                     │
│  Messages transmis: 3/4                             │
│  ✓ "Fracture du Cycle" — bien porté par OM-85       │
│  ✓ "Hiérarchie d'Évidence" — via les barres         │
│  ✓ "Axe Intestin-Poumon" — perception faible (18%)  │
│  ✗ "Spécificité par Couche" — jamais atteint        │
│                                                     │
│  Verdict: CONFUS (pression 1.02x)                   │
│  Le visuel contient plus que le lecteur ne peut      │
│  absorber en 5 secondes.                            │
│                                                     │
│  [Améliorer]  [Rejouer]  [System 2 (90s)]           │
└─────────────────────────────────────────────────────┘
```

This text IS the `generate_reading_narrative()` output — already implemented. We just display it nicely after the animation finishes, so the user has both the visual AND the verbal interpretation.

The three buttons at the bottom:
- **Améliorer** → calls `/analyze/improve/{slug}` (auto-improvement turn)
- **Rejouer** → replays the animation
- **System 2 (90s)** → runs the 90s sim and plays that animation (accelerated to ~10s playback)

---

## Burst + Halo Effects

### Burst (on saccade landing)
When the eye lands on a new node — a **particle burst** radiates from the center:
- 8-12 small circles (2px) explode outward from node center
- Color: same as the node's attention color (gold for high, blue for low)
- Duration: 400ms
- Scale: from 0 → node radius * 2, opacity: 1 → 0
- CSS: `@keyframes burst { from { transform: scale(0); opacity: 1; } to { transform: scale(2); opacity: 0; } }`
- Feels like an impact — the eye HIT this element

### Halo (during fixation)
While the eye fixates on a node — **concentric ripple rings** pulse outward:
- One new ring every 200ms of fixation
- Each ring: circle that scales from node radius → radius * 3, opacity 0.6 → 0
- Duration: 800ms per ring
- Color: node attention color at 30% opacity
- CSS: `@keyframes halo { from { r: {nodeRadius}; opacity: 0.6; } to { r: {nodeRadius*3}; opacity: 0; } }`
- Rings accumulate — longer fixation = more overlapping rings = stronger visual impression
- Feels like sonar — the element is being PROBED

### After fixation (residue)
When the eye leaves:
- Burst dissipates (already gone after 400ms)
- Last 2 halo rings remain visible at 15% opacity (permanent residue)
- The node keeps its attention color + soft glow
- The residue halos show "this was read" even after the eye moved on

### Implementation
All SVG — no Canvas needed:
```html
<!-- Burst: 8 particles -->
<g class="burst" style="animation: burst-fade 400ms ease-out forwards;">
  <circle cx="..." cy="..." r="2" fill="{color}" style="animation: burst-particle 400ms ease-out forwards; --angle: 0deg;"/>
  <circle cx="..." cy="..." r="2" fill="{color}" style="animation: burst-particle 400ms ease-out forwards; --angle: 45deg;"/>
  ...
</g>

<!-- Halo ring -->
<circle class="halo-ring" cx="..." cy="..." r="{nodeRadius}" fill="none"
        stroke="{color}" stroke-width="1.5" opacity="0.6"
        style="animation: halo-expand 800ms ease-out forwards;"/>
```

## Electric Link Particles

When a thing→narrative link transmits attention, the filament **comes alive** with streaming particles:

### Activation trigger
A link lights up when BOTH conditions are met:
1. The source thing node has been fixated (has attention)
2. The link weight > 0 (transmission exists)

### Particle stream
- Small bright dots (3px) spawn at the source node and travel along the link path toward the narrative
- Speed: `100 + link_weight * 200` px/s (faster = stronger transmission)
- Density: one particle every `200 / link_weight` ms
- Color: gold `#fbbf24` for successful transmission, fading to red `#ef4444` for penalized links (anti-pattern)
- Trail: each particle leaves a 50ms afterglow (opacity decay)
- CSS: `offset-path: path(...)` on `<circle>` elements, animated with `offset-distance: 0% → 100%`

### Electric tension
The filament itself vibrates — a subtle oscillation perpendicular to the path:
- SVG filter: `feTurbulence` + `feDisplacementMap` on the link `<line>`
- Intensity proportional to current flow (more particles = more vibration)
- Frequency: 3-5Hz
- Amplitude: 1-3px
- This makes the links feel ALIVE — like cables under high voltage

### Constant modulation (always-on, even before animation starts)
Active links are NEVER static. Even at rest, they breathe:

- **Intensity pulse**: `opacity: 0.6 + sin(t * 2) * 0.15` — subtle breathing at 2Hz
- **Width modulation**: `stroke-width: base + sin(t * 3 + phase) * 0.5` — each link has its own phase offset so they don't sync
- **Displacement ripple**: `feTurbulence baseFrequency` oscillates `0.01 ↔ 0.03` at 1Hz — the link path itself undulates
- **Particle speed variation**: `speed *= 0.8 + sin(t * 5) * 0.4` — particles accelerate and decelerate in waves
- **Color temperature shift**: gold shifts slightly warm→cool→warm (`hue-rotate: sin(t) * 5deg`) — alive, not mechanical

All modulations use `sin()` with different frequencies and phase offsets per link. No two links pulse in sync. The network feels like a **living organism** — breathing, flowing, conducting.

Heavy links (weight > 0.7): stronger modulation amplitude, faster base frequency.
Light links (weight < 0.3): barely visible modulation, slow, subtle.
The WEIGHT of the link dictates how much LIFE it shows.

### Dead links
Links that never activate (dead nodes, orphan narratives):
- Stay dark grey, no particles, no vibration
- Slight transparency (0.3 opacity)
- At the end of the animation, these dead links become the diagnostic — "these connections never fired"

### Convergence glow
Where 3+ active links converge on the same narrative (via different carrier things):
- The convergence point glows bright white-gold `#fff7ed`
- Particles accelerate as they approach the convergence
- A soft pulsing halo at the junction point
- This shows REDUNDANCY — the message is well-transmitted through multiple carriers

---

## Space Zones — Transmission Fields

Spaces (visual zones) are not just outlines — they are **energy fields** that light up as their children receive attention.

### Zone activation
- When the first thing inside a space gets fixated → the space border starts glowing teal
- As more things inside the space are fixated → the interior fills with a faint teal wash, intensity proportional to total attention inside
- `zone_intensity = sum(child_attention) / sum(child_weight)` → 0-1

### Transmission zone
When attention inside a space successfully transmits to a narrative:
- A pulse of gold light floods the space interior (200ms, fade out over 500ms)
- This is the "transmission event" — the MOMENT the message gets through
- Multiple transmissions = multiple pulses = the space VIBRATES with successful communication

### Space hue displacement — narrative distance
Each space has its own **hue identity** derived from its **narrative distance** to other spaces — NOT spatial position.

Two spaces carrying similar messages → similar hue. Two spaces with unrelated messages → distant hues.

Computation:
1. For each space, collect the `synthesis` text of linked narratives
2. Embed with sentence-transformers (already loaded at startup)
3. Compute pairwise cosine similarity between all space embeddings
4. Project to 1D via first principal component → `narrative_position` ∈ [0, 1]
5. Map to hue: `space_hue = 144 + narrative_position * 60` → range 144° (green-teal) to 204° (blue-teal)

Fallback (if embeddings unavailable): use space index order as proxy.

Relative to the main teal (#0d9488 = hue 174°):
- Narratively similar spaces cluster near 174° (same teal)
- Distant narratives diverge to 144° (warm green) or 204° (cool blue)

Applied via `filter: hue-rotate({offset}deg)` on the space's border + fill.

State transitions:
- Activating → hue SHIFTS toward gold (45°): `active_hue = lerp(space_hue, 45, transmission_ratio)`
- Dead → shifts toward red (0°): `dead_hue = lerp(space_hue, 0, 1.0)` over 1s
- Partial → stays at base hue but desaturated

The hue displacement creates **narrative identity** — zones carrying related messages feel similar, zones with different messages feel distinct. The viewer maps meaning by color before reading the words.

### Dead zone reveal
Spaces where NO thing was fixated:
- Stay dark — no border glow, no fill, no pulse
- At the end of the animation, a slow RED wash fades in (1s transition)
- A subtle `×` marker appears in the center
- This is the gut-punch moment — "this entire zone was invisible"

### Partial zone
Spaces where SOME things were fixated but the narrative wasn't fully transmitted:
- Amber border (not teal, not red)
- Faint amber interior
- At the end: an amber `⚠` marker
- "The reader SAW elements here but didn't GET the message"

---

## Key Decisions

1. **Client-side only** — the sim data is already computed. No streaming needed.
2. **requestAnimationFrame** — smooth 60fps, synced to display refresh
3. **CSS transitions** for sphere color changes (200ms ease) — not instant, feels organic
4. **Scale pulse** on active fixation (1.15x) — the eye "lands" on the element
5. **Progressive reveal** — the overlay starts grey, builds up color. The ABSENCE of color at the end is the dead zone diagnostic.
6. **Real-time by default** — 5s = 5s. The user experiences the reader's time pressure.
