# Algorithm — Graph Renderer

## A1: Data Assembly

```
INPUT:
  graph: L3 graph dict (nodes with bbox, links)
  sim_s1: reader sim result (system 1)
  image_path: path to original GA image

OUTPUT:
  render_data: dict ready for SVG template or PIL renderer

STEPS:
1. Load graph nodes, extract bbox for each
2. Load sim results: node_attention (heatmap), scanpath, narrative_details, dead_spaces
3. Load anti-patterns from graph metadata
4. Compute derived values:
   a. max_attention = max(node_attention.values())
   b. attention_ratio[n] = node_attention[n] / max_attention  (0-1)
   c. color[n] = interpolate_color(attention_ratio[n])
   d. radius[n] = 12 + node.weight * 28
   e. glow[n] = 4 + node.energy * 16
   f. opacity[n] = 0.4 + node.stability * 0.6
   g. border[n] = anti_pattern_type or "clean"
5. Compute link render data:
   a. For each link with weight >= 0.3:
      - start = bbox_center(source)
      - end = bbox_center(target)
      - width = 1 + link.weight * 3
      - is_gold = link is thing→narrative
      - particle_speed = link.weight (for animation)
6. Compute space outlines:
   a. For each space with bbox:
      - rect = bbox mapped to pixels
      - is_dead = space.id in sim.dead_spaces
      - border_color = red if dead, teal if visited
7. Compute scanpath:
   a. Ordered list of (node_id, timestamp_ms, position)
   b. Entry point = first node in scanpath
8. Compute narrative badges:
   a. For each thing node, list linked narratives with status (reached/missed/weak)

RETURN render_data dict with all above
```

## A2: SVG Renderer (Web)

```
INPUT: render_data + image_display_dimensions (width, height in px)
OUTPUT: SVG string (inline HTML)

TEMPLATE STRUCTURE:
<svg viewBox="0 0 {width} {height}" style="position:absolute;top:0;left:0;">
  <!-- Layer 1: Dim overlay -->
  <rect width="100%" height="100%" fill="rgba(10,14,26,0.35)"/>

  <!-- Layer 2: Space outlines -->
  <g class="layer-spaces">
    {% for space in spaces %}
    <rect x y width height rx="8"
          stroke="{teal|red}" stroke-width="1.5" fill="rgba(...,0.04)"
          stroke-dasharray="{4 if dead}"/>
    {% endfor %}
  </g>

  <!-- Layer 3: Links -->
  <g class="layer-links">
    {% for link in links %}
    <line x1 y1 x2 y2
          stroke="{gold|silver}" stroke-width="{width}"
          opacity="{0.8 if gold else 0.4}"/>
    {% endfor %}
  </g>

  <!-- Layer 4: Thing spheres -->
  <g class="layer-nodes">
    {% for node in things %}
    <circle cx cy r="{radius}"
            fill="{color}" opacity="{opacity}"
            stroke="{border_color}" stroke-width="{border_width}"
            style="filter:drop-shadow(0 0 {glow}px {color});">
      <title>{tooltip}</title>
    </circle>
    <!-- Narrative badges -->
    {% for badge in node.narrative_badges %}
    <circle cx+r cy+offset r="4" fill="{gold|red}"/>
    {% endfor %}
    {% endfor %}
  </g>

  <!-- Layer 5: Scanpath (hidden by default) -->
  <g class="layer-scanpath" style="display:none;">
    <polyline points="{scanpath_coords}" stroke="#f59e0b"
              stroke-width="2" stroke-dasharray="6 4" fill="none"/>
    {% for step in scanpath %}
    <text x y font-size="8" fill="#fbbf24">{step.time_ms}ms</text>
    {% endfor %}
    <!-- Entry point pulse -->
    <circle cx cy r="8" fill="none" stroke="#10b981" stroke-width="2">
      <animate attributeName="r" values="8;12;8" dur="2s" repeatCount="indefinite"/>
    </circle>
  </g>

  <!-- Layer 6: Problems (hidden by default) -->
  <g class="layer-problems" style="display:none;">
    {% for space in dead_spaces %}
    <rect x y width height fill="rgba(239,68,68,0.08)"/>
    {% endfor %}
    {% for node in skipped_nodes %}
    <text x y font-size="12" fill="#ef4444" text-anchor="middle">✗</text>
    {% endfor %}
  </g>
</svg>
```

## A3: PNG Renderer (Export)

```
INPUT: render_data + original image path
OUTPUT: PNG file (composite)

STEPS:
1. Open GA image with Pillow
2. Create overlay image (RGBA, same dimensions)
3. Draw dim layer: semi-transparent dark rectangle
4. Draw space outlines: PIL.ImageDraw.rectangle
5. Draw links: PIL.ImageDraw.line with width
6. Draw spheres: PIL.ImageDraw.ellipse with fill + border
7. Draw glow: second pass with larger radius, lower opacity
8. Draw narrative badges: small filled circles
9. Alpha composite overlay onto GA image
10. Save as PNG
```

## A4: Color Interpolation

```python
ANCHORS = [
    (0.0, (71, 85, 105)),    # grey  #475569
    (0.2, (59, 130, 246)),   # blue  #3b82f6
    (0.5, (45, 212, 191)),   # teal  #2dd4bf
    (0.8, (245, 158, 11)),   # amber #f59e0b
    (1.0, (251, 191, 36)),   # gold  #fbbf24
]

def attention_to_color(ratio):
    # Find surrounding anchors and lerp
    for i in range(len(ANCHORS) - 1):
        if ANCHORS[i][0] <= ratio <= ANCHORS[i+1][0]:
            t = (ratio - ANCHORS[i][0]) / (ANCHORS[i+1][0] - ANCHORS[i][0])
            r = int(ANCHORS[i][1][0] + t * (ANCHORS[i+1][1][0] - ANCHORS[i][1][0]))
            g = int(ANCHORS[i][1][1] + t * (ANCHORS[i+1][1][1] - ANCHORS[i][1][1]))
            b = int(ANCHORS[i][1][2] + t * (ANCHORS[i+1][1][2] - ANCHORS[i][1][2]))
            return (r, g, b)
    return ANCHORS[-1][1]
```

## A5: Integration with save_graph

```python
# In db.py _post_save_async():
# After reader sim + graph health:
try:
    from graph_renderer import render_overlay_png
    overlay_path = render_overlay_png(graph_dict, sim_s1, ga_image_path)
    # Update DB with overlay path
    db.execute("UPDATE ga_graphs SET overlay_path = ? WHERE id = ?", (overlay_path, gid))
except Exception as e:
    log.warning(f"Overlay render failed: {e}")
```

## A6: Integration with ga-detail

```python
# In app.py ga_detail route:
# After loading graph and sim:
overlay_svg = None
if latest_graph and latest_sim:
    from graph_renderer import render_overlay_svg
    overlay_svg = render_overlay_svg(latest_graph, latest_sim, image_width, image_height)
# Pass to template
"overlay_svg": overlay_svg,
```
