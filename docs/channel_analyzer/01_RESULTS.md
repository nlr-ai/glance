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

## R6: Anti-Pattern Detection

Each node is checked for 3 node-level anti-patterns, plus 1 GA-level anti-pattern:

| Type | Scope | Detection | Meaning | Example |
|------|-------|-----------|---------|---------|
| **fragile** | Node | Important node (w>=0.6) with < 2 visual channels | No redundancy — if the single channel fails (colorblind, thumbnail, fast scan), message is lost | "Immature Immune System" encoded only as text |
| **incongruent** | Node | Channels on same node point to OPPOSING semantic meanings | Brain receives contradictory signals — confusion, not hierarchy | Color says "danger" (red) but position says "positive result" (top-right, prominent) |
| **inverse** | Node | Important node (w>=0.8) but avg channel effectiveness < 0.5 | GA visually demotes something that should be prominent | Key finding buried in small gray text at bottom |
| **missing_category** | GA | An entire channel family (color, form, grouping, depth) has zero channels used | GA ignores a full perceptual dimension — reduces communicative bandwidth | All rectangles same size = missing "form" family |

**Severity for missing_category:** HIGH for color, form, grouping. MEDIUM for depth.

**Measurement:** `metadata.channel_analysis.anti_patterns[]` — list of `{node_id, type, detail}` for node-level, `{type: "missing_category", family, severity, detail}` for GA-level.

### Critical distinction: incongruent != warped

- **Warp** (existing GLANCE metric) = uneven WEIGHT distribution across nodes. Quantitative. "One element hogs all visual attention."
- **Incongruent** (new anti-pattern) = channels on a SINGLE node send opposing SEMANTIC signals. Qualitative. "The node says two things at once."

Warp is about between-node imbalance. Incongruence is about within-node conflict.

## Guarantee Loop

```
R1 (channel map) → SENSE (channel_analyzer.py output) → HEALTH (non-zero channels per node) → CARRIER (Silas/designer)
R5 (avg effectiveness) → SENSE (metadata.channel_analysis) → HEALTH (avg > 0.5) → CARRIER (iteration loop)
R6 (anti-patterns) → SENSE (anti_patterns[]) → HEALTH (0 inverse on w>=0.8 nodes) → CARRIER (Silas/designer)
R6 (missing_category) → SENSE (anti_patterns[type=missing_category]) → HEALTH (0 HIGH-severity missing families) → CARRIER (iteration loop)
```
