# GA Iteration Process — GLANCE Feedback Loop

## The Loop

```
GENERATE/MODIFY ──→ ANALYZE (Gemini Vision) ──→ L3 GRAPH
      ↑                                            │
      │                                            ▼
      │                                     ARCHETYPE + SCORES
      │                                            │
      │                                            ▼
      │                                   RECOMMENDATIONS
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
- Returns: nodes (5-15), links, metadata (chart_type, word_count, channels, hierarchy_clear, accessibility, executive_summary_fr)
- Saves: L3 graph YAML + raw response

### 3. Classify Archetype
```python
from archetype import classify_from_vision_metadata
arch = classify_from_vision_metadata(result['metadata'])
```
- 7 archetypes: Cristallin / Spectacle / Tresor Enfoui / Encyclopedie / Desequilibre / Embelli / Fantome
- Approximated scores: S10 (saliency), S9b (hierarchy), S2 coverage, Drift, Warp

### 4. Get Recommendations
```python
from recommender import analyze_ga
recs = analyze_ga(graph_path)
```
- Flags high-energy nodes (not visually resolved)
- Identifies strengths (high weight + high stability)
- Accessibility warnings
- Upgrade paths

### 5. Interpret & Apply Fixes
Read the graph like a diagnostic:
- **High energy (e > 0.7)** = element is "moving", not settled → needs visual anchoring
- **Low stability (s < 0.6)** = encoding is ambiguous → clarify channel
- **Low weight (w < 0.3)** = element is invisible → increase size/contrast or remove
- **hierarchy_clear: False** = the main message doesn't pop in 5s → restructure visual weight
- **word_count > 30** = too much text → cut labels

### 6. Re-render and Re-analyze
Compare V(n) vs V(n+1):
- Track: hierarchy_clear, word_count, node stability, energy reduction, archetype shift
- Target: Cristallin archetype, S9b >= 0.80, all node energies < 0.5

## Metrics to Track Per Version

| Metric | Target | Source |
|--------|--------|--------|
| hierarchy_clear | True | metadata |
| word_count | <= 30 | metadata |
| S9b (hierarchy) | >= 0.80 | archetype approx |
| S10 (saliency) | >= 0.60 | archetype approx |
| Archetype | Cristallin | classifier |
| Max node energy | < 0.50 | graph nodes |
| Accessibility issues | 0 | metadata |
| Node count | 8-12 | graph |
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
