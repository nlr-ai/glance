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
4. Extract argument_structure from the paper's logical flow:
   "Identify the argument chain: Problem → Evidence → Conclusion.
    For each argument node, specify:
    - id (arg_1, arg_2, ...)
    - type: problem | solution | evidence | mechanism | conclusion
    - claim_ids: which claims belong to this argument
    - description: one-sentence summary of this argument step
    - depends_on: list of arg_ids this step requires (upstream logic)
    - supports: list of arg_ids this step provides evidence for"

   → OUTPUT additions:
     claims_list: [...]          # (existing)
     argument_structure: [
       {id: "arg_1", type: "problem", claim_ids: [...], description: "...", depends_on: [], supports: []},
       {id: "arg_2", type: "solution", claim_ids: [...], description: "...", depends_on: ["arg_1"], supports: []},
       {id: "arg_3", type: "evidence", claim_ids: [...], description: "...", depends_on: [], supports: ["arg_2"]}
     ]
```

## A1.5: Validate Argument Chain

```
INPUT: argument_structure from A1
OUTPUT: validated argument chain (or FAIL with diagnostics)

PURPOSE: Narrative structure must be validated BEFORE visual design.
  A GA that encodes claims without argument coherence is a list, not a story.

STEPS:
1. Graph integrity check:
   - Every claim_id in claims_list must appear in at least one argument node
   - Every argument node must have at least one claim_id
   - No orphan arguments (every node except the root "problem" must have
     depends_on or supports linking it to the chain)

2. Chain completeness check:
   - There must be at least one "problem" type node (the anchor)
   - There must be at least one "conclusion" or "solution" type node
   - Every "evidence" node must support at least one other node
   - The chain must be traversable from problem → conclusion

3. Narrative extraction:
   - Walk the argument graph to produce intended_narratives:
     Each path from problem → conclusion = one intended narrative
   - Tag each narrative with its constituent claim_ids
   - Store as intended_narratives list for A2 comparison

4. If any check fails → RAISE with diagnostics:
   - Which claims are orphaned
   - Which argument nodes are disconnected
   - What paths are broken
   → Return to A1 for re-extraction (max 2 retries, then flag for human review)
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

PASS 4 — Narrative validation (match report):
  Compare intended_narratives (from A1.5) vs extracted_narratives (from vision analysis):
    For each intended_narrative:
      - Find best-matching extracted_narrative (by claim overlap)
      - Score: |matched_claims| / |intended_claims|
      - Status: FOUND (≥80%), PARTIAL (50-79%), WEAK (<50%), MISSING (0%)

  → Output: MATCH REPORT
    intended_narrative | matched_extracted | claim_overlap | status
    -------------------|-------------------|---------------|-------
    "problem→evidence" | "left_panel_flow"  | 4/5 (80%)     | FOUND
    "mechanism_chain"  | —                  | 0/3 (0%)      | MISSING

  → FAIL GATE: if >20% of intended_narratives have status MISSING,
    the GA cannot encode the paper's argument. Abort with diagnostics.
    → Return to A3/A4 to redesign visual carriers for missing narratives.
```

This is the key insight: the analysis must be HIERARCHICAL. The full image gives the structure. The per-space crops give the detail. The channels are analyzed at both levels. And the narrative validation ensures the argument chain is visually encoded.

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
   f. Argument chain traversal:
      For each relationship in argument_structure (depends_on, supports):
        - Identify the visual carriers for both the source and target argument
        - Verify a visual link exists between them (arrow, proximity, flow,
          shared color, containment, or other spatial/channel encoding)
        - Score: has_visual_carrier (yes/no)

      → FAIL GATE: if >20% of argument relationships have no visual carrier,
        the GA fails to encode the paper's logical flow.
        → Return to A5 (layout) or A4 (object design) to add missing links.

      → Output: ARGUMENT TRAVERSAL REPORT
        arg_source | arg_target | relationship | visual_carrier | status
        -----------|------------|-------------|----------------|-------
        arg_1      | arg_2      | depends_on  | arrow_panel_1  | OK
        arg_2      | arg_3      | supports    | —              | MISSING
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
