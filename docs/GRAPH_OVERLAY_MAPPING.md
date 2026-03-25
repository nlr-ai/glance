# GLANCE Graph Overlay — Mapping Data to Visuals

## Concept

The graph is rendered **on top of the GA image** as a transparent overlay. The reader sees the original figure with the mechanism superimposed — like X-ray vision revealing the internal structure of attention flow.

Every visual property encodes exactly one data dimension. No decoration. No redundancy. Every pixel communicates.

---

## Layer Stack (bottom to top)

```
1. GA Image (original, full resolution)
2. Dim overlay (rgba(10,14,26, 0.35)) — darkens the image so nodes pop
3. Space containers (bbox outlines)
4. Links (steel connectors + gold flows)
5. Thing nodes (positioned at bbox centers)
6. Narrative indicators (edge badges on linked things)
7. Scanpath trail (reader simulation)
8. Problem markers (anti-patterns, orphans)
```

---

## Node Mapping: Things (displayed)

Things are the only nodes rendered as circles on the overlay. They sit at the center of their bbox.

### Position
| Data | Visual |
|------|--------|
| `bbox [x,y,w,h]` | Node center = `(x + w/2, y + h/2)` mapped to image pixel coords |
| No bbox | Fallback: estimated from YAML order + space containment |

### Size = Weight (visual prominence)
```
radius = 12 + weight * 28    →  min 12px, max 40px
```
| weight | radius | meaning |
|--------|--------|---------|
| 0.2 | 18px | Minor element |
| 0.5 | 26px | Medium element |
| 0.8 | 34px | Dominant element |
| 1.0 | 40px | Primary focal point |

### Fill Color = Attention Received (from reader sim)

The core encoding. How much attention the reader sim allocated to this node, normalized to the max attention in the graph.

```
attention_ratio = node_attention / max_node_attention
```

| attention_ratio | Color | Hex | Meaning |
|----------------|-------|-----|---------|
| ≥ 0.8 | Bright gold | `#fbbf24` | Reader fixated here — high transmission |
| 0.5 – 0.8 | Warm amber | `#f59e0b` | Good attention, solid carrier |
| 0.2 – 0.5 | Cool teal | `#2dd4bf` | Moderate attention, functional |
| 0.01 – 0.2 | Steel blue | `#3b82f6` | Barely glanced at |
| 0 (skipped) | Cold grey | `#475569` | Never reached — invisible |

Gradient is continuous, not stepped. Interpolate between anchor colors.

### Border = Node Health

| Condition | Border | Width | Meaning |
|-----------|--------|-------|---------|
| Clean (no problems) | Same as fill, slightly darker | 2px | Healthy |
| Fragile anti-pattern | Red dashed | 2.5px `#ef4444` | Single-channel risk |
| Incongruent anti-pattern | Flickering red/amber | 2.5px animated | Conflicting signals |
| Inverse anti-pattern | Red solid + oversized node | 3px `#ef4444` | Important but invisible |
| Orphan (no narrative link) | Dim grey dotted | 1px `#64748b` | Visual noise |

### Glow = Energy (unresolved tension)

```
glow_radius = 4 + energy * 16    →  min 4px, max 20px
glow_opacity = 0.2 + energy * 0.4
```

| energy | glow | meaning |
|--------|------|---------|
| 0.0 | 4px, faint | Resolved — message clear |
| 0.5 | 12px, medium | Some tension — ambiguity |
| 1.0 | 20px, bright | High tension — unresolved, confusing |

Glow color matches fill color.

### Opacity = Stability

```
opacity = 0.4 + stability * 0.6    →  min 0.4, max 1.0
```

Low stability = translucent, uncertain. High stability = solid, definitive.

---

## Node Mapping: Spaces (displayed as containers)

Spaces are rendered as **bbox outlines** on the overlay — transparent panels that group their children.

### Shape
Rounded rectangle matching `bbox [x,y,w,h]`, mapped to image pixels.

### Border Color = Space Attention Health

Sum attention of all things inside this space.

| Space status | Border | Fill |
|-------------|--------|------|
| Well-visited (≥1 child got attention) | `#2dd4bf` teal, 1.5px solid | `rgba(45,212,191, 0.04)` |
| Dead (no child visited) | `#ef4444` red, 2px dashed | `rgba(239,68,68, 0.06)` |

### Label
Space name in small caps, top-left inside the bbox. Color matches border. Font 9px monospace.

---

## Node Mapping: Narratives (NOT displayed as nodes)

Narratives are **invisible**. They don't exist on the image — they are meanings that live INSIDE spaces and are carried by things. But their state is shown through their carriers.

### Narrative Health → Badges on Carrier Things

For each thing linked to a narrative, show a small **edge badge** indicating narrative health:

| Narrative status | Badge on carrier thing | Position |
|-----------------|----------------------|----------|
| Reached (attention > 0) | Small gold dot (4px) | Bottom-right of thing node |
| Reached but weak (< 30%) | Small amber dot (4px) | Bottom-right |
| Missed (0 attention) | Small red dot (4px) with `!` | Bottom-right |

If a thing carries multiple narratives: stack dots vertically (max 3 visible).

### Narrative Text (on hover/click)

When user hovers/clicks a thing node, a tooltip shows:
```
[Thing Name] (w=0.85, att=72%)
├─ ✓ "Treatment reduces infection" (92%)
├─ ⚠ "Mechanism involves IgA pathway" (18%)
└─ ✗ "Long-term safety profile" (0%)
```

---

## Link Mapping (displayed)

### Thing → Space (containment)
- **Hidden by default** — implied by position inside space bbox
- Only shown if thing is outside its linked space (broken containment)
- Style: thin grey dotted, 0.5px, `#334155`

### Thing → Thing (visual relation)
- **Thin steel connector**: `#64748b`, width = `1 + link_weight * 2`
- Straight line between node centers
- Only show links with weight ≥ 0.3 (avoid clutter)

### Thing → Narrative (transmission — the important one)
- **NOT drawn as visible links** (narratives aren't displayed)
- Instead: the gold/amber fill of the thing node IS the transmission indicator
- If a thing has high attention AND high link weight to narrative → gold
- If a thing has high attention BUT low link weight → amber (sees it, doesn't transmit)
- This is already encoded in the fill color via `transmitted = fixation * link_weight * efficiency`

---

## Scanpath Overlay (optional layer, toggle-able)

When activated, shows the reader sim trajectory:

### Path Line
- Gold dotted line connecting nodes in visit order
- Line segments: `#f59e0b`, 2px, dash `6 4`
- Arrows at each segment end (direction of eye movement)
- Timestamp labels at each node: `"300ms"` in 8px, `#fbbf24`

### Entry Point
- First visited node gets a pulsing green ring (the eye enters here)
- `#10b981`, 3px, animation: scale 1.0→1.3→1.0 over 2s

### Fixation Halos
- Concentric rings around each visited node
- Number of rings = visit count (1-3)
- Ring radius = time spent (ms) / 100
- Color matches node fill, opacity decreasing outward

### Dead Zone Overlay
- Unvisited spaces get a dark red wash: `rgba(239,68,68, 0.08)`
- Unvisited things get a small `×` marker in `#ef4444`, 8px

---

## Aggregate Indicators (top bar or side panel)

| Indicator | Visual | Data |
|-----------|--------|------|
| **Clarity score** | Large number + verdict | archetype proxy score |
| **Coverage** | `14/17` with mini bar | nodes visited / total |
| **Narrative hit rate** | `3/4` with dots (gold/red) | narratives reached / total |
| **Pressure** | Gauge `1.02x` | budget_pressure |
| **Verdict** | Text badge colored | Limpide / Clair / Ambigu / Confus / Obscur / Incompréhensible |
| **Dead zones** | Count in red | dead_space_count |

---

## Composite Summary: What Each Visual Property Encodes

| Visual Property | Data Dimension | Source |
|----------------|---------------|--------|
| **Node position** | Physical location on GA | bbox from Gemini |
| **Node size** | Visual prominence | weight |
| **Node fill color** | Attention received | reader_sim heatmap |
| **Node border** | Health / anti-patterns | channel_analyzer |
| **Node glow radius** | Unresolved tension | energy |
| **Node opacity** | Clarity / certainty | stability |
| **Gold dot badge** | Narrative reached | reader_sim narrative_attention |
| **Red dot badge** | Narrative missed | reader_sim orphan_narratives |
| **Space border color** | Zone visited or dead | reader_sim dead_spaces |
| **Link thickness** | Relationship strength | link weight |
| **Scanpath line** | Reading order | reader_sim scanpath |
| **Fixation halos** | Time spent | reader_sim visit_count × tick_ms |
| **Dead zone wash** | Never seen | reader_sim skipped_nodes |
| **Aggregate bar** | Overall quality | composite score |

---

## Anti-Pattern Visual Summary

| Problem | What user sees on overlay |
|---------|--------------------------|
| **Fragile** (1 channel) | Red dashed border on thing + tooltip "1 seul canal" |
| **Incongruent** (conflicting signals) | Border flickers red↔amber + tooltip "signaux contradictoires" |
| **Inverse** (important but invisible) | Large node (high weight) but cold blue/grey fill (no attention) — the contradiction IS the signal |
| **Orphan thing** (no narrative) | Ghost node: opacity 0.3, grey, no glow — "bruit visuel" |
| **Orphan narrative** (no carrier) | Red `!` badge floats in the space where the narrative lives — "message sans porteur" |
| **Dead space** (no visited children) | Space border turns red dashed, interior gets dark wash |
| **Budget overload** | Pressure gauge in red, last nodes in scanpath have `×` markers |

---

## Interaction Model (web)

| Action | Effect |
|--------|--------|
| **Hover thing** | Show tooltip: name, weight, attention%, linked narratives with status |
| **Hover space** | Highlight all children, show space name + visit status |
| **Click thing** | Expand detail panel: all channels, anti-patterns, recommendations for this node |
| **Toggle "Scanpath"** | Show/hide the reader simulation trajectory |
| **Toggle "Problems"** | Show/hide anti-pattern markers |
| **Slider "Time"** | Scrub through the 5s scanpath (nodes light up in sequence) |
| **Play button** | Animate the full scanpath in real-time (5s) or accelerated (1s) |

---

## Rendering Priority

If too many elements overlap:
1. Always show thing nodes (they are THE content)
2. Show space borders only if bbox data exists
3. Show scanpath only on toggle
4. Hide thing→thing links below weight 0.5
5. Aggregate narrative badges if >3 on one node
6. Label only the top 5 nodes by weight (others on hover)
