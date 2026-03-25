# Health — Graph Renderer

## H1: Overlay Exists for Every Graphed GA

```
RESULT: Every GA with a graph in DB has an overlay PNG
SENSE: SELECT COUNT(*) FROM ga_graphs WHERE overlay_path IS NULL AND id IN (SELECT graph_id FROM reading_simulations)
HEALTH: count = 0
CARRIER: admin dashboard shows "Overlays: X/Y"
```

## H2: SVG Renders Without Error

```
RESULT: ga-detail page shows overlay SVG for any GA with graph + sim
SENSE: HTTP GET /ga-detail/{slug} → response contains '<svg class="graph-overlay"'
HEALTH: no 500 errors on ga-detail for graphed GAs
CARRIER: server logs, error rate monitoring
```

## H3: Color Mapping Consistency

```
RESULT: attention_to_color(0.0) = grey, attention_to_color(1.0) = gold
SENSE: unit test on the interpolation function
HEALTH: all anchor points produce exact expected RGB values
CARRIER: test suite
```

## H4: Overlay Render Time

```
RESULT: PNG overlay renders in <2 seconds for a 15-node graph
SENSE: timer in render_overlay_png
HEALTH: p95 < 2s
CARRIER: log line with duration
```
