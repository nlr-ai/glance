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

## A5: Anti-Pattern Detection

Runs after step 5 of A1 (graph enrichment), on the enriched graph. Pure graph math — no LLM call.

```
INPUT: Enriched L3 graph (nodes with visual_channels[] and channel_score)
OUTPUT: metadata.channel_analysis.anti_patterns[]

For each node in graph:
  w = node.weight
  channels = node.visual_channels
  score = node.channel_score

  1. FRAGILE check
     IF w >= 0.6 AND len(channels) < 2:
       → emit {node_id, type: "fragile", detail: "w={w}, channels={len(channels)}"}

  2. INVERSE check
     IF w >= 0.8 AND score < 0.5:
       → emit {node_id, type: "inverse", detail: "w={w}, channel_score={score}"}

  3. INCONGRUENT check
     For each pair (ch_a, ch_b) in channels:
       IF ch_a.semantic_direction OPPOSES ch_b.semantic_direction:
         → emit {node_id, type: "incongruent", detail: "{ch_a.channel} vs {ch_b.channel}"}

     Semantic opposition is detected by Gemini during batch analysis (A2).
     Each channel response includes an optional `semantic_direction` field:
       - "positive", "negative", "neutral", "hierarchical", "danger", "emphasis"
     Opposition pairs: positive/negative, danger/positive, emphasis/negative.
```

### Detection order matters

Fragile and inverse are pure numeric — deterministic, zero ambiguity. Incongruent requires semantic interpretation from the Gemini batch response. If `semantic_direction` is absent, incongruent detection is skipped for that channel pair.

## A4: CLI Usage

```bash
python channel_analyzer.py <image_path> <graph_yaml> [--output enriched.yaml]

# Example:
python channel_analyzer.py ga_library/immunomod.png data/immunomod_graph.yaml
# → saves data/immunomod_graph_enriched.yaml
```
