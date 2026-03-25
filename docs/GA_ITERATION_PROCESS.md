# GA Iteration Process — GLANCE Feedback Loop

## The Loop

```
GENERATE/MODIFY ──→ ANALYZE (Gemini Vision) ──→ L3 GRAPH (space/narrative/thing)
      ↑                                            │
      │                                            ▼
      │                                     ARCHETYPE + SCORES
      │                                            │
      │                                            ▼
      │                                   READER SIMULATION
      │                                   (Z-pattern traversal)
      │                                            │
      │                                            ▼
      │                                   AUTO-IMPROVE PROMPTS
      │                                   (FACT→PROBLEM→QUESTION)
      │                                            │
      └────────── APPLY FIXES ◄────────────────────┘
```

## Steps

### 1. Generate or modify the GA
- Parametric compositor (svgwrite + YAML configs)
- Output: SVG → PNG (full + delivery)

### 2. Run through GLANCE Vision Pipeline
```python
from vision_scorer import analyze_ga_image
result = analyze_ga_image(image_bytes, filename="ga_vX.png")
```
- Gemini Pro Vision receives the image + structured YAML prompt
- Stratified 4-step extraction:
  1. **Zones** — `space` nodes: bounded visual containers/regions on the GA
  2. **Messages** — `narrative` nodes: intended reader takeaways or effects
  3. **Elements** — `thing` nodes: concrete visual elements (bars, icons, text, shapes)
  4. **Links** — typed relationships:
     - thing → narrative = "this element CARRIES this message"
     - thing → space = "this element LIVES IN this zone"
     - narrative → space = "this message is communicated IN this zone"
     - thing → thing = visual relationships (proximity, alignment, etc.)
- Returns: nodes (spaces + narratives + things), links, metadata (chart_type, word_count, channels, hierarchy_clear, accessibility, executive_summary_fr)
- Saves: L3 graph YAML + raw response

### 3. Classify Archetype
```python
from archetype import classify_from_vision_metadata
arch = classify_from_vision_metadata(result['metadata'])
```
- 7 archetypes: Cristallin / Spectacle / Tresor Enfoui / Encyclopedie / Desequilibre / Embelli / Fantome
- Approximated scores: S10 (saliency), S9b (hierarchy), S2 coverage, Drift, Warp

### 4. Reader Simulation + Recommendations
```python
from recommender import analyze_ga
recs = analyze_ga(graph_path)
```
- **Reader simulation:** a virtual actor traverses `space` nodes in Z-pattern (top-left → bottom-right)
  - Time per space is proportional to the space's weight
  - Attention propagates: actor → things in space → narratives linked to those things
  - Each narrative accumulates `received_attention` from elements that carry it
- **Metrics derived:**
  - `received_attention` per narrative — did the message actually get carried?
  - `diversity` — are narratives spread across spaces or clustered?
  - `route_exists` — can the reader reach every narrative through the Z-pattern?
- Accessibility warnings
- Upgrade paths

### 5. Interpret & Apply Fixes
Read the graph like a diagnostic:
- **Narrative with low received_attention** = message isn't carried by enough visual elements → add/strengthen thing→narrative links
- **Space with no narratives** = zone exists visually but communicates nothing → add narrative or merge into adjacent space
- **Thing not linked to any narrative** = decorative element → justify or remove
- **Low diversity** = all messages clustered in one zone → redistribute across spaces
- **route_exists: False** = reader's Z-pattern skips a narrative entirely → reposition elements
- **hierarchy_clear: False** = the main message doesn't pop in 5s → restructure visual weight
- **word_count > 30** = too much text → cut labels

### 6. Re-render and Re-analyze
Compare V(n) vs V(n+1):
- Track: hierarchy_clear, word_count, narrative received_attention, diversity, route_exists, archetype shift
- Target: Cristallin archetype, S9b >= 0.80, all narratives reachable, min narrative attention > 0.20

## Auto-Improve Prompts

When generating improvement prompts for Gemini, follow the FACT → PROBLEM → QUESTION structure:

1. **FACT** — Specific diagnosis with node names and values from the graph (e.g., "narrative:key_finding has received_attention=0.12, carried by only 1 thing node")
2. **PROBLEM** — Dynamic problem description using actual graph data (e.g., "The key finding is invisible because it lives in space:bottom_zone which the Z-pattern reaches last, and its single carrier has weight=0.2")
3. **QUESTION** — Open question for Gemini to explore (e.g., "How can we increase the key finding's visibility without adding clutter?")

## Metrics to Track Per Version

| Metric | Target | Source |
|--------|--------|--------|
| hierarchy_clear | True | metadata |
| word_count | <= 30 | metadata |
| S9b (hierarchy) | >= 0.80 | archetype approx |
| S10 (saliency) | >= 0.60 | archetype approx |
| Archetype | Cristallin | classifier |
| All narratives reachable | True | reader sim (route_exists) |
| Min narrative attention | > 0.20 | reader sim (received_attention) |
| Narrative diversity | > 0.50 | reader sim |
| Accessibility issues | 0 | metadata |
| Node count (spaces) | 2-5 | graph (space nodes) |
| Node count (narratives) | 3-7 | graph (narrative nodes) |
| Node count (things) | 5-15 | graph (thing nodes) |
| Link count | >= nodes-2 | graph |

## Blog Display Format

For each version iteration:
- Thumbnail of the GA
- GLANCE archetype badge + score
- Delta table (what changed)
- **Top recommendation** that drove the next iteration (the proof that analysis guides development)

### Narrative arc for the GLANCE paper GA:

| Version | Top Reco (from graph) | What it triggered |
|---------|----------------------|-------------------|
| V1 | "No visual hierarchy — bars alone don't communicate the problem" | V2: add scissors graph (engagement vs comprehension) |
| V2 | "No methodological context — reader doesn't know what this measures" | V3: add magnifying lens (Visual Spin) + 5.0s chronometer |
| V3 | "Labels overflow — text competes with visual elements" | V4: move labels below bars, fix spacing |
| V4 | "Low contrast on pink background — Comprehension label barely visible" | V5: boost contrast, add annotation "6 RCTs · 538 participants" |
| V5 | "S9b=0.70 (target ≥0.80), 6/11 nodes high energy (not resolved)" | V6: gradient shine on GLANCE bar, ×7.7 multiplier, grid lines, bigger chrono |
| V6 | "Word count 31, Comprehension label still flagged, Engagement energy 0.9" | V7: ... |

This narrative proves GLANCE is not just a score — it's an **iterative design tool**. The graph tells you exactly what to fix next.
