# Validation — Channel Analyzer

## V1: Every Node Gets Channels

After enrichment, every node in the L3 graph MUST have a `visual_channels` list (may be empty if the node is not visually encoded). No node is silently skipped.

## V2: Effectiveness Bounds

All `effectiveness` values MUST be in [0.0, 1.0]. Values outside this range are clamped and logged as warnings.

## V3: Channel Score Consistency

`node.channel_score` MUST equal `mean(node.visual_channels[].effectiveness)`. If `visual_channels` is empty, `channel_score` MUST be 0.0.

## V4: Anti-Pattern Thresholds Are Non-Negotiable

| Anti-pattern | Scope | Condition | Invariant |
|--------------|-------|-----------|-----------|
| **fragile** | Node | `w >= 0.6 AND len(channels) < 2` | Every node meeting this condition MUST be flagged |
| **inverse** | Node | `w >= 0.8 AND channel_score < 0.5` | Every node meeting this condition MUST be flagged |
| **incongruent** | Node | Opposing semantic directions on same node | Flagged only when `semantic_direction` data is present |
| **missing_category** | GA | Entire channel family has zero used channels | Every empty family MUST be flagged; severity HIGH for color/form/grouping, MEDIUM for depth |

## V5: No Duplicate Anti-Patterns

A node MUST NOT have two anti-pattern entries of the same type. One entry per type per node maximum. For GA-level anti-patterns (missing_category), one entry per family maximum.

## V6: Anti-Pattern List Completeness

`metadata.channel_analysis.anti_patterns` MUST be present after enrichment (may be empty list). Its absence is a pipeline bug.

## V7: Incongruent Requires Evidence

An incongruent anti-pattern MUST reference exactly two channels with opposing semantic directions. If `semantic_direction` is missing from Gemini output, no incongruent flag is emitted — never inferred.

## V8: Warp Independence

Anti-pattern detection MUST NOT read or depend on the GLANCE warp metric. They measure different phenomena (within-node conflict vs between-node imbalance) and must remain independent.

## V9: Inter-Batch Healing Invariants

- After each batch's validate step, all effectiveness values MUST be in [0.0, 1.0]. No unclamped values may propagate to the next batch.
- The graph_yaml sent to batch N+1 MUST contain the enrichment from batches 1..N. Sending stale (un-enriched) graph to later batches is a pipeline bug.
- Final anti-pattern detection (A5) MUST run on the fully merged graph, not on any intermediate partial enrichment.

## V10: Missing Category Exhaustiveness

The 4 channel families (color, form, grouping, depth) MUST all be checked. If the channel catalog adds a new family, the missing_category check MUST be updated to include it.
