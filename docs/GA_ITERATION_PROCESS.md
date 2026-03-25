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
- Key recommendation that drove the next iteration
