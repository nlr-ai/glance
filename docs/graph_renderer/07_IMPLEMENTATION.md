# Implementation — Graph Renderer

## Files

| File | Role | Lines (est.) |
|------|------|-------------|
| `graph_renderer.py` | Core: data assembly + PIL PNG renderer + SVG string generator | ~400 |
| `templates/_graph_overlay.html` | Jinja2 SVG template for inline web overlay | ~100 |
| `db.py` | Add `overlay_path` column to `ga_graphs` | ~5 |
| `app.py` | Pass overlay_svg to ga-detail template | ~10 |
| `templates/ga_detail.html` | Toggle buttons + overlay container | ~30 |

## graph_renderer.py

```
Functions:
  assemble_render_data(graph, sim_result, image_size) → dict
  render_overlay_svg(graph, sim_result, width, height) → str (SVG)
  render_overlay_png(graph, sim_result, image_path) → str (path to PNG)
  attention_to_color(ratio) → (r, g, b)
  _node_position(node, image_w, image_h) → (px_x, px_y)
  _node_radius(weight) → px
  _node_glow(energy) → px
  _link_width(weight) → px
```

## Dependencies

- `Pillow` (PIL) — already in requirements, for PNG rendering
- `Jinja2` — already in requirements, for SVG template
- No new dependencies

## DB Migration

```sql
ALTER TABLE ga_graphs ADD COLUMN overlay_path TEXT;
```

## Integration Points

1. `db.py:_post_save_async()` → call `render_overlay_png()` after sim
2. `app.py:ga_detail()` → call `render_overlay_svg()` and pass to template
3. `templates/ga_detail.html` → render SVG overlay + toggle buttons
