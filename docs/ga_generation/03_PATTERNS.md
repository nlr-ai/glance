# Patterns — GA Generation V2

## P1: AI as Teacher, SVG as Student

The gen AI produces reference images. The parametric system LEARNS from them — extracting the information channels used, not the pixels. The SVG student implements the same channels with different rendering.

The AI image is NEVER the deliverable. It's the training data.

## P2: Six Data Families

Every scientific GA encodes data from these families. The extraction step must identify which families are present in each paper:

| Family | Encoding type | Example channel | Example |
|--------|--------------|-----------------|---------|
| Quantitative | Proportional | length, area | Evidence bars (18 vs 5 RCTs) |
| Spatial | Positional | position, layer | Anatomical localization |
| Ordinal | Sequential | order, flow | Cascade (macrophage → DC → T cell) |
| Directional | Gradient | color gradient, position | Pathological → Protected |
| Semi-quantitative | Density | density, saturation | Viral load decreasing |
| Categorical | Binary/nominal | icon, shape | Symptomatic vs Protected |

## P3: Channel Delta, Not Pixel Delta

Convergence is measured per information channel:

```
delta(channel_i) = |AI_channel_i - SVG_channel_i|

Where channel properties are:
  - used: bool (is this channel active?)
  - effectiveness: 0-1 (how well does it transmit?)
  - semantic_direction: what does it communicate?
```

If the AI uses "texture=granular" to encode "bacterial" and the SVG uses "pattern=dots" to encode "bacterial", the semantic direction matches even though the rendering differs. Delta = low.

## P4: Object Learning Cycle

```
10 AI variants → extract channel vectors → PCA → parameter space
    → code SVG object with sliders on principal axes
    → optimize sliders via reader sim
    → object joins library
```

Each object has:
- `draw(params) → SVG group`
- `param_ranges` (learned from AI variants)
- `channels_implemented` (which info channels this object can encode)
- `channels_ai_only` (which channels need AI rendering, can't be SVG)

## P5: Channel Discovery

When channel_analyzer finds a channel in the AI image that's NOT in the 70-channel ontology:

1. Name it (Gemini proposes a name + description)
2. Classify it (family: color/form/grouping/depth/texture/...)
3. Assess SVG-implementability (can feTurbulence/feBlend/pattern do it?)
4. If yes → add to ontology + implement in the object
5. If no → flag as "AI-only channel" (the SVG can't reproduce this exact effect)

## P6: Compositional Assembly

The GA is assembled from library objects positioned on a layout grid:

```
GA = layout_grid + Σ(object_i(params_i) at position_i)
```

Objects don't know about each other. The layout grid handles spacing, alignment, and visual hierarchy. The reader sim validates that the assembled whole transmits the intended narratives.

## P7: Two-Pass Optimization

1. **Layout pass** — optimize positions and sizes (hill climb on reader sim, <1ms per eval)
2. **Channel pass** — optimize per-object params to minimize channel delta with AI reference (channel_analyzer comparison)

Layout pass is cheap (graph-only, no image). Channel pass is expensive (needs rendering + analysis).
