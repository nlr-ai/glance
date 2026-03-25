# Implementation — Channel Analyzer

## Files

| File | Role |
|------|------|
| `channel_analyzer.py` | Main script — load catalog, batch Gemini calls, enrich graph |
| `data/visual_channel_catalog.md` | 70+ visual channels with speed/communicates/relevance |

## Key Functions

| Function | Purpose |
|----------|---------|
| `load_channel_catalog()` | Parse markdown catalog → list of channel dicts |
| `batch_channels(channels, 25)` | Split into batches of 25 |
| `analyze_batch(image, graph, channels, model)` | Send 1 batch to Gemini, parse YAML response |
| `enrich_graph(graph, results)` | Merge channel annotations into graph nodes |
| `analyze_ga_channels(image, graph, output)` | Full pipeline orchestrator |

## Dependencies

- `google.generativeai` — Gemini Pro Vision API
- `pyyaml` — graph I/O
- `visual_channel_catalog.md` — channel definitions

## Data Flow

```
visual_channel_catalog.md → load_channel_catalog() → 70 channels
                                                         │
GA image + L3 graph ──→ analyze_batch() × 3 ──→ channel results
                                                         │
                                                    enrich_graph()
                                                         │
                                                    enriched YAML
```

## Output Schema (per node)

```yaml
nodes:
  - id: "thing:1"
    name: "GLANCE Comprehension Bar"
    weight: 1.0
    stability: 1.0
    energy: 0.5
    visual_channels:
      - channel: "color_luminance"
        effectiveness: 0.9
        role: "dark teal = high certainty"
      - channel: "size_length"
        effectiveness: 1.0
        role: "bar length encodes comprehension rate"
    channel_score: 0.95  # avg effectiveness
```

## Cost

~3 Gemini Pro Vision calls per GA (70 channels / 25 per batch). At ~$0.01/call = ~$0.03 per GA analysis.
