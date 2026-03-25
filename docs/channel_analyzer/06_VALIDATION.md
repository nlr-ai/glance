# Validation — Channel Analyzer

## V1: Every Node Gets Channels

After enrichment, every node in the L3 graph MUST have a `visual_channels` list (may be empty if the node is not visually encoded). No node is silently skipped.

## V2: Effectiveness Bounds

All `effectiveness` values MUST be in [0.0, 1.0]. Values outside this range are clamped and logged as warnings.

## V3: Channel Score Consistency

`node.channel_score` MUST equal `mean(node.visual_channels[].effectiveness)`. If `visual_channels` is empty, `channel_score` MUST be 0.0.

## V4: Anti-Pattern Thresholds Are Non-Negotiable

| Anti-pattern | Condition | Invariant |
|--------------|-----------|-----------|
| **fragile** | `w >= 0.6 AND len(channels) < 2` | Every node meeting this condition MUST be flagged |
| **inverse** | `w >= 0.8 AND channel_score < 0.5` | Every node meeting this condition MUST be flagged |
| **incongruent** | Opposing semantic directions on same node | Flagged only when `semantic_direction` data is present |

## V5: No Duplicate Anti-Patterns

A node MUST NOT have two anti-pattern entries of the same type. One entry per type per node maximum.

## V6: Anti-Pattern List Completeness

`metadata.channel_analysis.anti_patterns` MUST be present after enrichment (may be empty list). Its absence is a pipeline bug.

## V7: Incongruent Requires Evidence

An incongruent anti-pattern MUST reference exactly two channels with opposing semantic directions. If `semantic_direction` is missing from Gemini output, no incongruent flag is emitted — never inferred.

## V8: Warp Independence

Anti-pattern detection MUST NOT read or depend on the GLANCE warp metric. They measure different phenomena (within-node conflict vs between-node imbalance) and must remain independent.
