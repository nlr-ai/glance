# Results — Channel Analyzer

## R1: Channel Usage Map
Every node in a GA's L3 graph is annotated with which visual channels encode it, and how effectively.

**Measurement:** `node.visual_channels[]` list with per-channel effectiveness 0-1.

## R2: Channel Score per Node
Each node gets a `channel_score` = average effectiveness across all channels encoding it.

**Measurement:** `node.channel_score` (0-1 float).

## R3: Missed Opportunities
Channels that are NOT used but SHOULD be, based on the node's role and the channel's communicative power.

**Measurement:** `metadata.channel_analysis.missed_opportunities` count.

## R4: Low Effectiveness Flags
Channels that ARE used but poorly (effectiveness < 0.5) — these are the priority fixes.

**Measurement:** `metadata.channel_analysis.low_effectiveness` count.

## R5: Global Channel Effectiveness
Average effectiveness across all used channels — the GA's "visual transmission quality".

**Measurement:** `metadata.channel_analysis.avg_effectiveness` (0-1).

## Guarantee Loop

```
R1 (channel map) → SENSE (channel_analyzer.py output) → HEALTH (non-zero channels per node) → CARRIER (Silas/designer)
R5 (avg effectiveness) → SENSE (metadata.channel_analysis) → HEALTH (avg > 0.5) → CARRIER (iteration loop)
```
