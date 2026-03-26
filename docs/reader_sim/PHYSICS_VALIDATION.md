# Reader Simulation — Physics Validation

## Purpose

Sanity check: for each expected real-world reading behavior, does the graph math + physics produce the correct effect?

Each entry follows:
- **Behavior**: what happens in reality when a reader scans a GA for 5 seconds
- **Graph representation**: which node/link properties encode this
- **Physics formula**: what the sim computes
- **Expected effect**: what should happen in the simulation
- **Actual effect**: what happens now
- **Verdict**: VALID / PARTIAL / NOT MODELED

---

## B1: Heavier elements attract more attention

**Behavior**: Larger, bolder, higher-contrast visual elements are fixated longer by readers.

**Graph**: `thing.weight` (0-1). Higher weight = more visually prominent.

**Physics**:
```
ideal_ticks[n] = fixation_budget * weight[n] / sum(weights)
fixation_strength = actor_attention * weight
```

**Expected**: High-weight nodes get more fixation time and produce more attention.

**Actual**: Proportional allocation gives more ticks to high-weight nodes. `fixation_strength` is also weight-scaled, so attention output scales quadratically with weight (more ticks * higher strength per tick).

**Verdict**: VALID

---

## B2: Complex GAs overwhelm the reader

**Behavior**: Information overload — too many elements means the reader can't absorb everything in 5 seconds. Some elements are never seen.

**Graph**: Number of `thing` nodes. Each node needs fixation ticks + saccade ticks.

**Physics**:
```
saccade_budget = n_things - 1          (1 tick per transition)
fixation_budget = total_ticks - saccade_budget
budget_pressure = (saccades + fixation_alloc) / total_ticks
```

When `budget_pressure > 1.0`: last nodes in Z-order are SKIPPED (TIMEOUT).

**Expected**: GAs with many elements should predict skipped nodes.

**Actual**: 17-thing immunomod graph → pressure=1.02x, last node ("Label 'Protected airways'") truncated. GA flagged OVERLOADED.

**Verdict**: VALID

---

## B3: Incoherence slows the reader

**Behavior**: When a visual element sends contradictory signals (e.g., red color = danger BUT round shape = friendly), the reader hesitates. Processing time increases, comprehension decreases.

**Graph**: `incongruent` anti-pattern on thing node. Two channels with opposing `semantic_direction` (e.g., positive/negative, danger/positive).

**Physics**: Currently NONE.

```python
# Current: incongruent nodes get same allocation as coherent nodes
fixation_strength = actor_attention * weight  # no penalty
```

**Expected**: Incongruent nodes should:
- Cost MORE fixation time (hesitation penalty) — reader stalls
- Transmit LESS to linked narratives (confusion reduces comprehension)

**Proposed fix**:
```python
# On a node with incongruent anti-pattern:
# Full penalty if incongruent TO the narrative (channels contradict the message)
# Half penalty if incongruent visually but still supporting the narrative
if incongruent_to_narrative:
    incongruent_penalty = 0.5   # full penalty — channels fight the message
    flag = f"incongruent BECAUSE: {explain_conflict(thing, narrative)}"
else:
    incongruent_penalty = 0.75  # half penalty — visual clash, narrative intact
    flag = f"incongruent BECAUSE: visual conflict only — {explain_conflict(thing)}"
fixation_strength = actor_attention * weight * incongruent_penalty
# But the node still consumes its full allocated ticks (hesitation = wasted time)
# Flag is attached to the result for diagnostic traceability
thing_result["incongruent_flag"] = flag
```

Effect: the node ABSORBS attention (ticks used) but TRANSMITS less to narratives. Time is wasted on confusion. This matches the real behavior: the reader stares at the element but doesn't understand it. The flag explains WHY the incongruence was detected, making diagnostic review actionable. The two-tier penalty distinguishes between visual-only clashes (reader hesitates but still gets the message) and narrative-level contradictions (reader is actively confused about the meaning).

**Verdict**: NOT MODELED → TO ADJUST

---

## B4: Fragile encoding = element easily missed

**Behavior**: If information is carried by only one visual channel (e.g., only color hue), it's vulnerable: color-blind readers miss it, thumbnails lose it, low-contrast screens hide it. The element exists but fails to transmit.

**Graph**: `fragile` anti-pattern (thing.weight >= 0.6 AND len(visual_channels) < 2).

**Physics**: Currently NONE.

```python
# Current: fragile nodes transmit at full strength
transmitted = fixation_strength * link_weight  # no discount
```

**Expected**: Fragile nodes should transmit LESS to narratives (single channel = less robust signal = lower probability of message reception). However, fragility is narrative-dependent: a single channel that is semantically appropriate for the narrative's role is NOT fragile. E.g., encoding "anatomy location" by color alone is robust (part of reader's domain knowledge), but encoding "evidence strength" by color alone is fragile (arbitrary mapping).

**Proposed fix**:
```python
# Fragile discount on narrative transmission — narrative-context-aware
n_channels = len(thing.get("visual_channels", []))
channel_robustness = min(n_channels / 3, 1.0)  # 1 channel=0.33, 2=0.67, 3+=1.0

# Narrative context override: if the single channel is semantically native
# to the narrative's domain, fragility is reduced
if n_channels == 1 and is_domain_native(thing, linked_narrative):
    channel_robustness = 0.8  # override: domain knowledge compensates fragility

transmitted = fixation_strength * link_weight * channel_robustness
```

Effect: a fragile element (1 channel) only transmits 33% of its fixation to narratives by default. But if the channel is semantically appropriate for the narrative's role (e.g., spatial color in anatomy, size for quantity), the penalty is softened to 80%. The reader SAW it, and domain knowledge fills in the gaps. Without that domain match, the message didn't fully register because it was encoded on a single fragile channel with no semantic anchor.

**Verdict**: NOT MODELED → TO ADJUST

---

## B5: Inverse pattern — important but visually weak

**Behavior**: A concept that matters scientifically (high weight) but has low visual salience (small, pale, poorly encoded) gets overlooked by the reader.

**Graph**: `inverse` anti-pattern (thing.weight >= 0.8 AND thing.channel_score < 0.5).

**Physics**: PARTIAL.

```python
# Current: weight drives allocation AND fixation strength
ideal_ticks = fixation_budget * weight / sum(weights)
fixation_strength = actor_attention * weight
```

Problem: `weight` here is used for both IMPORTANCE and VISUAL SALIENCE. But in an inverse pattern, these diverge: the element is important (should carry a message) but not visually salient (won't actually attract the eye).

**Expected**: The sim should separate importance from salience. An inverse node should get LESS fixation time (low salience = eye skips it) despite being important.

**Proposed fix**:
```python
# Use channel_score as visual salience proxy
salience = thing.get("channel_score", thing.get("weight", 0.5))
ideal_ticks = fixation_budget * salience / sum(saliences)
# But fixation_strength still uses weight (the science is important)
fixation_strength = actor_attention * weight
```

Effect: low channel_score → fewer ticks → less total attention, even though each tick is "strong" (high weight). The reader spends less time because the element doesn't attract the eye, but what little time is spent is meaningful.

Alternative: keep current V1, flag the deficit in results.

**Verdict**: PARTIAL → TO ADJUST (V2)

---

## B6: Z-pattern scanning

**Behavior**: Western readers scan left→right, top→bottom. Elements in the top-left are seen first; bottom-right elements may be skipped if attention is exhausted.

**Graph**: Estimated positions from YAML order + space containment.

**Physics**:
```python
# Z-order sort: y-row first (quantized to 3 rows), then x
def _z_order_key(node_id, positions):
    pos = positions.get(node_id, (0.5, 0.5))
    row = int(pos[1] * 3)
    return (row, pos[0])
```

**Expected**: Top-left nodes visited first with full attention. Bottom-right nodes visited last, may be skipped.

**Actual**: Nodes sorted by Z-order, visited sequentially. First nodes get full `actor_attention`, last nodes may TIMEOUT.

**Verdict**: VALID

---

## B7: Saccade distance costs effort

**Behavior**: Large eye jumps (saccades) between distant elements are more effortful and take more time than small saccades to nearby elements.

**Graph**: Distance between estimated positions.

**Physics**: Currently FLAT.

```python
# Current: every saccade costs exactly 1 tick, regardless of distance
tick += 1  # same cost for 0.03 and 0.90 distance
```

**Expected**: Longer saccades should cost more (2-3 ticks for cross-GA jumps vs 1 tick for nearby elements).

**Proposed fix** (V2):
```python
saccade_ticks = max(1, round(dist * 3))  # 1-3 ticks based on distance
```

**Actual**: In the immunomod test, all saccades are 0.037 distance (nodes tightly packed as orphans). So the flat cost is indistinguishable from proportional cost. This will matter when space-based layout creates real distance variation.

**Verdict**: PARTIAL → acceptable for V1, TO ADJUST for V2

---

## B8: Attention fatigue over time

**Behavior**: After 3-4 seconds of sustained scanning, the reader's attention degrades. Late-seen elements receive less effective processing even if the reader looks at them.

**Graph**: N/A (temporal phenomenon, not graph property).

**Physics**: Currently NONE.

```python
# Current: actor_attention = 1.0 for the entire simulation
# No decay applied in V1
fixation_strength = actor_attention * weight  # actor_attention always 1.0
```

**Expected**: `actor_attention` should decay over ticks, so late-visited nodes produce weaker fixation even with same weight.

**Proposed fix** (V2):
```python
# After each fixation tick:
actor_attention *= 0.97  # 3% decay per tick
# After 50 ticks: 1.0 * 0.97^50 = 0.218 = 78% attention lost
```

**Actual**: Without decay, a node visited at tick 45 produces same fixation_strength as one at tick 0 (given same weight). This is unrealistic but simplifies V1 analysis.

**Verdict**: NOT MODELED → TO ADJUST (V2)

---

## B9: Messages need visual carriers

**Behavior**: A narrative (desired effect: "reader understands X") is only received if carried by a visible element (thing). No visual carrier → invisible message.

**Graph**: `thing → narrative` links with weight. Narrative nodes without incoming links from things = orphan narratives.

**Physics**:
```python
for neighbor, link_w in adj.get(thing_id, []):
    if neighbor.startswith("narrative:"):
        transmitted = fixation_strength * link_w
        narrative_attention[neighbor] += transmitted
```

**Expected**: Narratives with no thing→narrative links get 0 attention. Narratives carried by high-weight things with strong links get high attention.

**Actual**: Orphan narratives correctly identified and flagged. In immunomod test: 4/4 narratives got 0% because thing→narrative links are missing from graph.

**Verdict**: VALID

---

## B10: Dead spaces are invisible

**Behavior**: Visual zones (spaces) that contain no salient elements are never looked at. The reader's eye has no reason to go there.

**Graph**: `space` nodes. Things linked to spaces via `thing → space` links. Spaces with no child things = dead.

**Physics**:
```python
visited_spaces = set()
for link in links:
    src, tgt = link["source"], link["target"]
    if src in node_attention and tgt.startswith("space:"):
        visited_spaces.add(tgt)
dead_spaces = [s for s in spaces if s["id"] not in visited_spaces]
```

**Expected**: Spaces with no visited children are flagged as dead zones.

**Actual**: Immunomod test: 3/3 spaces dead (thing→space containment links missing from graph). When links exist, correctly identifies dead vs visited.

**Verdict**: VALID

---

## B11: Redundancy protects messages

**Behavior**: A message carried by 3 independent visual elements is more robust than one carried by a single element. If the reader misses one carrier, others may still transmit.

**Graph**: Multiple `thing → narrative` links to same narrative. `diversity` metric in graph_health.

**Physics**:
```python
# Narrative receives attention from ALL things that link to it
for thing_id in visited_things:
    for neighbor, link_w in adj.get(thing_id, []):
        if neighbor == narrative_id:
            narrative_attention[narrative_id] += fixation_strength * link_w
```

**Expected**: More carriers → higher cumulative narrative attention. Even if one carrier is skipped (TIMEOUT), others may still transmit.

**Actual**: Naturally handled. Each thing→narrative link independently contributes. Redundancy = more total attention.

**Verdict**: VALID

---

## B12: Proximity/grouping = perceived relatedness

**Behavior**: Spatially close elements (Gestalt proximity) are perceived as belonging together. Things in the same visual zone are processed as a group.

**Graph**: Things linked to same space cluster spatially.

**Physics**:
```python
# Position estimation clusters children around parent space center
angle = 2 * math.pi * j / max(len(children), 1)
spread = 0.3 / cols
child_x = cx + spread * math.cos(angle)
child_y = cy + spread * math.sin(angle)
```

**Expected**: Things in the same space are visited sequentially (close in Z-order). Things in different spaces require longer saccades.

**Actual**: Position estimation produces spatial clustering. Z-order groups nearby things together.

**Verdict**: VALID

---

## B13: Title/header is seen first

**Behavior**: The title is almost always the first fixation point. It anchors interpretation of everything else.

**Graph**: Title thing nodes typically at top of YAML (→ top of Z-order) with high weight.

**Physics**: Z-order puts top-positioned nodes first. First node gets full attention with no saccade cost.

**Expected**: Title fixated first and longest.

**Actual**: In immunomod test, OM-85 (first in YAML) gets first fixation. Depending on graph structure, title may not be first — depends on position estimation from YAML order.

**Verdict**: VALID (assuming Gemini outputs title first in YAML)

---

## B14: Narrative Coherence

**Behavior**: The reader follows a logical sequence matching the paper's argument. A well-structured GA guides the eye through Problem → Solution → Evidence → Implications. Broken chains (skipped steps) reduce comprehension; complete chains produce a coherent mental model.

**Graph**: `narrative` nodes linked by directed edges (`narrative → narrative` links) representing argumentative flow. Each link carries `relation_kind` or semantic direction indicating the argument step (e.g., problem→solution, solution→evidence, evidence→implications). Orphan narratives have no incoming or outgoing argument-flow links.

**Physics**: Currently NONE.

```python
# Current: narratives receive attention independently from their carriers
# No concept of argument chains or traversal order
narrative_attention[narrative_id] += transmitted  # no chain awareness
```

**Expected**: Full chains traversed (all links in a Problem→Solution→Evidence→Implications sequence visited) should produce higher `narrative_attention` than orphan narratives or broken chains. Narrative coherence emerges from sequential traversal — the reader builds understanding step by step.

**Proposed fix**:
```python
# Compute argument coverage: % of narrative chains fully traversed
chains = extract_argument_chains(narratives, narrative_links)
# e.g., chains = [[n_problem, n_solution, n_evidence, n_implications], ...]

chains_completed = 0
for chain in chains:
    visited = [n for n in chain if narrative_attention.get(n, 0) > 0]
    if len(visited) == len(chain):
        chains_completed += 1
        # Bonus: chain completion reinforces all members
        for n in chain:
            narrative_attention[n] *= 1.2  # coherence bonus

sequence_fidelity = chains_completed / max(len(chains), 1)
argument_coverage = len(all_chain_nodes_visited) / max(len(all_chain_nodes), 1)

# Penalize skipped links: if a chain has gaps, downstream nodes lose attention
for chain in chains:
    for i, node in enumerate(chain):
        if i > 0 and narrative_attention.get(chain[i-1], 0) == 0:
            # Previous link was skipped — penalize this node
            narrative_attention[node] *= 0.5  # broken chain penalty
```

Effect: narratives that belong to complete argument chains get a coherence bonus (1.2x). Narratives downstream of a skipped step are penalized (0.5x) — the reader can't understand the evidence if they missed the problem statement. `sequence_fidelity` measures what fraction of the paper's argument was fully conveyed. `argument_coverage` measures raw traversal.

**Verdict**: NOT MODELED → TO ADJUST (P0)

---

## Summary Table

| # | Behavior | Graph Math | Physics | Verdict |
|---|----------|-----------|---------|---------|
| B1 | Heavy elements → more attention | `weight` → `ideal_ticks = budget * w / Σw` | Proportional allocation | VALID |
| B2 | Too many elements → overload | `n_things` → `pressure = (saccades + fixation) / budget` | TIMEOUT on late nodes | VALID |
| B3 | Incoherence → confusion | `incongruent` anti-pattern | No effect on sim | NOT MODELED |
| B4 | Fragile encoding → missed | `fragile` anti-pattern | No effect on sim | NOT MODELED |
| B5 | Important but invisible | `inverse` anti-pattern, `channel_score` | Weight used for both importance & salience | PARTIAL |
| B6 | Z-pattern scanning | Estimated positions | Z-order sort | VALID |
| B7 | Distant saccades cost more | Position distance | Flat 1 tick per saccade | PARTIAL |
| B8 | Attention fatigue | Temporal (not graph) | No decay | NOT MODELED |
| B9 | Messages need carriers | `thing→narrative` links | Propagation through links | VALID |
| B10 | Dead spaces invisible | `space` nodes, containment links | Visited-space tracking | VALID |
| B11 | Redundancy protects | Multiple `thing→narrative` links | Cumulative attention | VALID |
| B12 | Proximity = grouping | Space-based clustering | Position estimation | VALID |
| B13 | Title seen first | YAML order, position | Z-order priority | VALID |
| B14 | Narrative coherence | Directed `narrative→narrative` chains | `argument_coverage`, `sequence_fidelity` | NOT MODELED |

**Score: 9/14 VALID, 2/14 PARTIAL, 4/14 NOT MODELED (but 1 is V2-only)**

---

## Priority Adjustments

### P0: Narrative coherence (B14) — CRITICAL
Argument chains must be modeled to measure whether the GA communicates its scientific story, not just individual data points.
```python
chains = extract_argument_chains(narratives, narrative_links)
sequence_fidelity = chains_completed / total_chains
# Weight narratives by position in argument chain
# Penalize skipped links (broken chain penalty = 0.5x downstream)
```

### P1: Incongruent penalty (B3) — HIGH
Anti-patterns already detected by channel_analyzer. Just need to read them in reader_sim and apply penalty. Two-tier: full penalty (0.5x) if incongruent to narrative, half penalty (0.75x) if visual-only conflict.
```python
if "incongruent" in thing_anti_patterns:
    if incongruent_to_narrative:
        transmission_efficiency *= 0.5   # full — channels fight the message
    else:
        transmission_efficiency *= 0.75  # half — visual clash, narrative intact
    flag = f"incongruent BECAUSE: {explain_conflict(thing, narrative)}"
    # ticks still consumed (hesitation)
```

### P2: Fragile discount (B4) — HIGH
Channel count already available on enriched graphs. Narrative-context-aware: single channels that are domain-native get reduced penalty (0.8 instead of 0.33).
```python
n_channels = len(thing.get("visual_channels", []))
channel_robustness = min(n_channels / 3, 1.0)
if n_channels == 1 and is_domain_native(thing, linked_narrative):
    channel_robustness = 0.8  # domain knowledge compensates
transmission_efficiency *= channel_robustness
```

### P3: Inverse salience split (B5) — MEDIUM
Requires separating `weight` (importance) from `channel_score` (visual salience) in allocation.
```python
salience = thing.get("channel_score", weight)  # fallback to weight if no channel data
ideal_ticks = budget * salience / sum(saliences)
```

### P4: Fatigue decay (B8) — MEDIUM (V2)
Simple exponential decay.
```python
actor_attention *= 0.97  # per tick
```

### P5: Distance-proportional saccades (B7) — LOW (V2)
```python
saccade_ticks = max(1, round(dist * 3))
```

---

## Calibration Constants (to validate with N=10 human testers)

| Constant | Current V1 | Proposed V2 | What it controls |
|----------|-----------|-------------|------------------|
| `tick_ms` | 100 | 100 | Time resolution |
| `total_ticks` | 50 | 50 | Total reading time (5s) |
| `saccade_cost` | 1 tick (flat) | `max(1, round(dist*3))` | Eye movement cost |
| `fatigue_decay` | 1.0 (none) | 0.97/tick | Attention loss over time |
| `incongruent_penalty` | 1.0 (none) | 0.5 | Confusion reduces transmission |
| `fragile_discount` | 1.0 (none) | `min(n_channels/3, 1)` | Single-channel vulnerability |
| `revisit_penalty` | N/A (no revisits) | 0.5x | Diminishing returns on re-fixation |
| `z_row_quantization` | 3 rows | 3 rows | Z-pattern scan line resolution |
| `narrative_weight_factor` | 1.0 (flat) | 1.5x primary / 1.0x secondary / 0.8x orphan | Multiplier on thing weight based on narrative role |

`narrative_weight_factor` governs how much a thing's narrative role amplifies its effective weight in the simulation. A thing carrying a primary narrative (first in argument chain, or sole carrier of a key message) gets 1.5x weight. Secondary narrative carriers get 1.0x (no change). Orphan things (no narrative link) get 0.8x — they exist visually but carry no message, so they should attract less simulated attention than message-bearing elements.

All constants are testable: compare sim predictions vs human verbal recall (S2 test).
Match = sim calibrated. Mismatch = adjust constant.
