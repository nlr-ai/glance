# Algorithm — Channel Analyzer

## A1: Main Pipeline

The L3 graph now contains 3 node types: `space` (visual zones), `narrative` (messages/effects), and `thing` (concrete visual elements). Channel analysis applies primarily to `thing` nodes (the visual elements that carry channels), but results propagate to `narrative` and `space` nodes through their links.

```
INPUT: GA image (PNG/JPG) + L3 graph (YAML with space/narrative/thing nodes)
OUTPUT: Enriched L3 graph with channel annotations

1. Load visual channel catalog (data/visual_channel_catalog.md)
   → Parse markdown into list of channel dicts
   → ~70 channels with: id, name, communicates, speed, glance_relevance

2. Split channels into batches of 25
   → 3 batches for 70 channels

3. For each batch (with inter-batch self-healing — see A6):
   a. Format prompt with:
      - GA image (multimodal)
      - L3 graph as YAML (updated with prior batch results)
      - 25 channel descriptions
   b. Send to Gemini Pro Vision
   c. Parse YAML response
   d. Extract per-channel: used, effectiveness, nodes_affected, issues, recommendation
      - nodes_affected references thing nodes (the visual carriers)
      - effectiveness on a thing propagates to its linked narratives
   e. Validate + heal + feed back (A6) before next batch
   f. Rate limit: 4s between batches

4. Final merge of all batch results (post-healing)

5. Enrich graph:
   a. For each thing node: attach visual_channels[] with channel + effectiveness + role
   b. Compute channel_score per thing node = avg(effectiveness)
   c. Propagate to narratives: for each narrative, aggregate channel_scores
      from thing nodes linked via thing→narrative ("carries") relationships
   d. Propagate to spaces: for each space, aggregate channel_scores
      from thing nodes linked via thing→space ("lives in") relationships
   e. Compute metadata.channel_analysis summary:
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
- The current L3 graph with typed nodes (space/narrative/thing) and their relationships
- 25 channel descriptions (name + communicates + speed)

Gemini returns per-channel YAML with:
- `used: true/false`
- `effectiveness: 0.0-1.0`
- `nodes_affected: [{node_id, role}]` — references `thing` nodes only
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

  4. MISSING_CATEGORY check (GA-level, runs once after all nodes)
     channel_families = {
       "color":    [channels whose family == "color"],
       "form":     [channels whose family == "form"],
       "grouping": [channels whose family == "grouping"],
       "depth":    [channels whose family == "depth"]
     }
     For each family in channel_families:
       used_in_family = [ch for ch in family if ch.used == true]
       IF len(used_in_family) == 0:
         severity = "HIGH" if family in ("color", "form", "grouping") else "MEDIUM"
         → emit {type: "missing_category", family: family, severity: severity,
                 detail: "zero channels used in {family} family"}
```

### Detection order matters

Fragile, inverse, and missing_category are pure numeric — deterministic, zero ambiguity. Incongruent requires semantic interpretation from the Gemini batch response. If `semantic_direction` is absent, incongruent detection is skipped for that channel pair.

Missing_category runs at GA scope (once), not per-node. It is appended to the same `anti_patterns[]` list.

## A6: Inter-Batch Self-Healing

Between Gemini batches, a validate-heal-feedback cycle prevents drift and ensures each batch builds on accumulated context.

```
For batch_index in 1..N:
  results = send_batch(batch_index)

  1. VALIDATE
     - Clamp all effectiveness values to [0.0, 1.0]
     - Fill missing fields with defaults (used: false, effectiveness: 0.0)
     - Log warnings for any clamped/filled values

  2. HEAL
     - Enrich graph partially: attach visual_channels[] from this batch's results
     - Recompute channel_score per affected node (running average)
     - Update metadata.channel_analysis counters (channels_used, low_effectiveness)

  3. FEED BACK
     - Serialize updated graph_yaml with partial enrichment
     - Pass updated graph_yaml to next batch prompt
     - Gemini sees accumulated channel annotations from prior batches
     - This gives Gemini cross-batch context (e.g., knows color channels were already found)

After all batches: run final merge + A5 anti-pattern detection on fully enriched graph.
```

### Why this matters

Without self-healing, each batch operates in isolation. Batch 3 might re-flag issues already addressed by batch 1's annotations, or miss interactions between channels analyzed in different batches. The feedback loop ensures monotonically improving context.

## A4: CLI Usage

```bash
python channel_analyzer.py <image_path> <graph_yaml> [--output enriched.yaml]

# Example:
python channel_analyzer.py ga_library/immunomod.png data/immunomod_graph.yaml
# → saves data/immunomod_graph_enriched.yaml
```
