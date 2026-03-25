# Algorithm — GA Generation V2

## A1: Paper → Attribute Extraction

```
INPUT: paper abstract text (+ optional full text, data tables)
OUTPUT: structured YAML spec with all data families

STEPS:
1. Send abstract to Gemini:
   "Extract all claims that must be visually encoded in a Graphical Abstract.
    For each claim, classify by data family:
    - quantitative (proportional values)
    - spatial (anatomical/positional)
    - ordinal (sequential/causal)
    - directional (gradient/transformation)
    - semi-quantitative (relative density/intensity)
    - categorical (binary/nominal)

    For each claim, specify:
    - the exact values to encode
    - the scientific source (which sentence in the abstract)
    - the priority (primary message vs supporting detail)"

2. Parse Gemini YAML response → validated claim list
3. Link claims to narrative nodes (claim_id → narrative_id)
```

## A2: Multi-Resolution Analysis (Image → Per-Space)

```
INPUT: GA image
OUTPUT: hierarchical graph (root + per-space detail)

PASS 1 — Full image analysis:
  analyze_ga_image(full_image)
  → root graph: 2-5 spaces, 2-4 narratives, 5-12 things
  → this is the MACRO structure

PASS 2 — Per-space analysis (automatic, triggered by save_graph):
  For each space with bbox:
    crop = crop_image(full_image, space.bbox)
    child_graph = analyze_ga_image(crop, prior_graph=space_context)
    → 5-12 sub-things within this space
    → finer detail: individual bars, icons, labels, arrows

  Merge child graphs into parent (deepen() function)
  → total: 30-60 nodes at resolution R=1

PASS 3 — Channel analysis on each level:
  analyze_channels(full_image, root_graph)      → macro channels
  For each space:
    analyze_channels(crop, child_graph)          → micro channels per zone

  → channel coverage at both macro and micro level
  → anti-patterns detected at BOTH resolutions
```

This is the key insight: the analysis must be HIERARCHICAL. The full image gives the structure. The per-space crops give the detail. The channels are analyzed at both levels.

## A3: AI Reference Generation

```
INPUT: claim list + data families from A1
OUTPUT: N reference images per object/concept

For each major concept in the GA (e.g., "PMBL mechanism"):
  1. Build a prompt from the claim data:
     "Scientific illustration of {concept}: {description}.
      Must encode: {list of channels this concept needs}.
      Style: clean scientific illustration, white background."

  2. Generate N=5-10 variants (different seeds/styles)

  3. Analyze each variant:
     For each variant:
       graph = analyze_ga_image(variant)
       channels = analyze_channels(variant, graph)
       → extract: which channels encode what information

  4. Build parameter space:
     Stack all channel vectors → matrix (N × C)
     PCA → find principal axes of variation
     Centroid → the "typical" version
     Ranges → min/max per parameter across variants
```

## A4: Parametric Object Learning

```
INPUT: N analyzed AI variants of one concept
OUTPUT: a parametric SVG function with learned ranges

STEPS:
1. From the channel analysis of N variants, extract common patterns:
   - What shape family? (circle, rect, organic curve, compound)
   - What color range? (hue ± spread)
   - What sub-element count? (min, max, typical)
   - What connection type? (arrow, contact, envelop, bridge)
   - What texture? (smooth, granular, striped, none)

2. Code the SVG function:
   def draw_concept(x, y, scale, detail, color, orientation, ...):
       # params have LEARNED ranges from AI variants
       # not arbitrary — bounded by what the AI produced

3. For each channel the AI used:
   a. Can SVG implement it?
      - feTurbulence → texture ✓
      - feGaussianBlur → glow/depth ✓
      - pattern → repetitive motif ✓
      - linearGradient → directional encoding ✓
      - clipPath + bezier → organic shape ✓
   b. If yes → implement in draw_concept()
   c. If no → flag as "AI-only channel", document what's lost

4. Measure channel delta:
   render SVG object → analyze_channels(render) → compare with AI channels
   → delta per channel
   → iterate on SVG implementation until delta < 0.3 on critical channels
```

## A5: Layout Optimization (Hill Climb)

```
INPUT: list of objects + layout grid + narrative priorities
OUTPUT: optimized positions/sizes

The layout is a YAML with positions and sizes for each object.
The reader sim runs on the GRAPH (not the image) → <1ms per eval.

ALGORITHM:
  1. Initialize layout from AI reference (or template)
  2. For each of 1000 iterations:
     a. Pick random param (position, size, spacing)
     b. Perturb by small delta
     c. Update graph node bbox/weight accordingly
     d. Run reader_sim(graph) → narrative_coverage
     e. If coverage improved → keep perturbation
     f. Else → revert

  3. Result: layout that maximizes narrative coverage

  COST: 1000 × 1ms = 1 second total. Zero API calls.
```

## A6: Assembly + Validation

```
INPUT: optimized layout + parametric objects
OUTPUT: final GA (SVG + PNG)

1. Render each object at its optimized position/size
2. Compose into single SVG
3. Render to PNG (Playwright or Pillow)
4. VALIDATE:
   a. analyze_ga_image(final_png) → graph
   b. Compare graph with intended narratives
   c. reader_sim(graph) → coverage must be ≥ target
   d. analyze_channels(final_png, graph) → no critical anti-patterns
   e. Check: each paper claim has a narrative with coverage > 50%
5. If validation fails → identify weakest link → iterate (back to A5 or A4)
```

## A7: Audit Chain Generation

```
For the final GA, produce an audit document:

Paper claim | GA narrative | Carrier things | Channels used | Reader coverage
------------|-------------|----------------|---------------|----------------
"OM-85 has 18 RCTs" | "Evidence hierarchy" | bar_om85 | length (β=1.0) | 92%
"PMBL repairs barrier" | "Mechanism" | pmbl_mech | position, form | 67%
...

Every row is a traceable link from paper → perception.
Rows with coverage < 50% are flagged as WEAK.
Rows with 0% are flagged as MISSING.
Claims without any row are flagged as OMITTED.
```
