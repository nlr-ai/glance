# Implementation — GA Iteration Process

## Current state

The iteration process exists as a manual workflow orchestrated by Silas using 4 independent scripts. No unified iteration runner script exists yet.

## Tools and dependencies

| Tool | Role | Location |
|------|------|----------|
| vision_scorer.py | Gemini Pro Vision -> L3 graph + metadata | `glance/vision_scorer.py` |
| archetype.py | 7-archetype classifier from scores or vision metadata | `glance/archetype.py` |
| recommender.py | Graph-based recommendations + channel upgrade paths | `glance/recommender.py` |
| compose_paper_ga.py | Parametric SVG compositor (YAML config driven) | `glance/ga_paper/compose_paper_ga.py` |

External dependencies:
- `google-generativeai` — Gemini API client (vision_scorer)
- `svgwrite` — SVG generation (compositor)
- `pyyaml` — YAML parsing throughout
- `Pillow` — PNG rendering from SVG (via vec_lib.render_png)

All Python, native Windows, no Docker.

## File map

### Core pipeline files

| File | Role in iteration |
|------|-------------------|
| `glance/vision_scorer.py` | Step 2: sends image to Gemini Vision, parses YAML response, validates L3 graph, saves to `data/` |
| `glance/archetype.py` | Step 3: `classify_from_vision_metadata()` approximates scores from metadata, `classify_ga()` does rule+distance classification |
| `glance/recommender.py` | Step 4: `analyze_ga()` walks graph nodes, flags high-energy/unstable nodes, runs accessibility checks, surfaces upgrade paths |
| `glance/ga_paper/compose_paper_ga.py` | Step 1/7: parametric compositor reads `config/layout.yaml` + `config/palette.yaml`, outputs SVG+PNG |
| `glance/ga_paper/config/layout.yaml` | Layout parameters — zones, positions, sizes |
| `glance/ga_paper/config/palette.yaml` | Color palette — all colors as named references |

### Data flow

```
config/*.yaml --[compose_paper_ga.py]--> output/*.svg + *.png
                                              |
                                              v
                                   [vision_scorer.py] ---> data/*_ga_graph.yaml
                                                                |
                                              +--------+--------+
                                              |                 |
                                     [archetype.py]    [recommender.py]
                                              |                 |
                                              v                 v
                                        archetype +     recommendations
                                        scores          + strengths
                                              |                 |
                                              +--------+--------+
                                                       |
                                                       v
                                              Human/AI applies fixes
                                                       |
                                                       v
                                              config/*.yaml (modified)
                                                       |
                                                       v
                                              Loop back to compose
```

### Key functions

| Function | File | Role in iteration |
|----------|------|-------------------|
| `analyze_ga_image()` | vision_scorer.py | Entry point: bytes -> validated graph + metadata + saved YAML |
| `_parse_gemini_yaml()` | vision_scorer.py | Robust YAML parsing with truncation recovery |
| `_validate_graph()` | vision_scorer.py | Clamp node properties, validate structure |
| `classify_from_vision_metadata()` | archetype.py | Approximate scores from metadata -> archetype |
| `classify_ga()` | archetype.py | Rule-based + distance-fallback classification |
| `analyze_ga()` | recommender.py | Walk graph, generate recommendations + strengths |
| `generate_report()` | recommender.py | Markdown report from analysis |
| `get_plain_text()` | recommender.py | Plain-language French translation of recommendations |
| `load_config()` | compose_paper_ga.py | Load layout + palette YAML configs |

### Missing (future)

| Component | Purpose |
|-----------|---------|
| `iterate_ga.py` | Unified iteration runner: analyze -> classify -> recommend -> compare -> log |
| `iteration_log.yaml` | Per-GA version history with delta tables |
| `compare_versions()` | Function to compute delta table between two version analyses |
