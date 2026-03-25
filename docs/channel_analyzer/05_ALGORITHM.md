# Algorithm — Channel Analyzer

## A1: Main Pipeline

```
INPUT: GA image (PNG/JPG) + L3 graph (YAML)
OUTPUT: Enriched L3 graph with channel annotations

1. Load visual channel catalog (data/visual_channel_catalog.md)
   → Parse markdown into list of channel dicts
   → ~70 channels with: id, name, communicates, speed, glance_relevance

2. Split channels into batches of 25
   → 3 batches for 70 channels

3. For each batch:
   a. Format prompt with:
      - GA image (multimodal)
      - L3 graph as YAML
      - 25 channel descriptions
   b. Send to Gemini Pro Vision
   c. Parse YAML response
   d. Extract per-channel: used, effectiveness, nodes_affected, issues, recommendation
   e. Rate limit: 4s between batches

4. Merge all batch results

5. Enrich graph:
   a. For each node: attach visual_channels[] with channel + effectiveness + role
   b. Compute channel_score per node = avg(effectiveness)
   c. Compute metadata.channel_analysis summary:
      - total_channels_analyzed
      - channels_used / unused
      - low_effectiveness count
      - missed_opportunities count
      - avg_effectiveness

6. Save enriched graph as {original}_enriched.yaml
```

## A2: Batch Prompt Structure

Each batch sends to Gemini:
- System context: "analyze this GA against these 25 visual channels"
- The GA image
- The current L3 graph (so Gemini knows what nodes exist)
- 25 channel descriptions (name + communicates + speed)

Gemini returns per-channel YAML with:
- `used: true/false`
- `effectiveness: 0.0-1.0`
- `nodes_affected: [{node_id, role}]`
- `issues: string`
- `recommendation: string`

## A3: Integration with GA Iteration Loop

```
GENERATE GA → ANALYZE (vision_scorer) → L3 GRAPH
                                            │
                                            ▼
                                    CHANNEL ANALYZER
                                            │
                                            ▼
                                    ENRICHED L3 GRAPH
                                            │
                                    ┌───────┴────────┐
                                    ▼                ▼
                              RECOMMENDER      COMPARE (vs ref)
                                    │                │
                                    ▼                ▼
                              FIX PRIORITIES    CONVERGENCE %
                                    │
                                    ▼
                              NEXT ITERATION
```

## A4: CLI Usage

```bash
python channel_analyzer.py <image_path> <graph_yaml> [--output enriched.yaml]

# Example:
python channel_analyzer.py ga_library/immunomod.png data/immunomod_graph.yaml
# → saves data/immunomod_graph_enriched.yaml
```
