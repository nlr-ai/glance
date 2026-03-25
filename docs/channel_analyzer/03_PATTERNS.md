# Patterns — Channel Analyzer

## P1: Enrich, Don't Score

The channel analyzer produces a **map**, not a number. Each node gets a list of channels with effectiveness — the downstream recommender and iteration loop decide what to do with it. Scoring is a separate concern.

## P2: Graph Math First, LLM Second

Fragile and inverse anti-patterns are pure numeric checks on weight and channel count. No LLM needed. Only incongruent detection depends on semantic interpretation from Gemini. If the LLM data is absent, the deterministic checks still run.

## P3: One Channel = One Measurement

Every channel annotation has exactly one effectiveness score (0-1). No composite scores, no "overall channel quality" fudge. The `channel_score` per node is a simple average — transparent and decomposable.

## P4: Anti-Patterns Are Structural, Not Aesthetic

The 3 anti-pattern types detect **information transmission failures**, not design preferences:
- **Fragile:** single point of failure in encoding
- **Incongruent:** contradictory signals on the same node
- **Inverse:** visual weight contradicts informational weight

These are bugs in the communication channel, not style opinions.

## P5: Warp vs Incongruence — Different Axes

Warp measures **between-node** weight imbalance (quantitative, existing GLANCE metric). Incongruence measures **within-node** channel conflict (qualitative, new). They are orthogonal. A GA can have zero warp but severe incongruence, or vice versa.

## P6: Batch Architecture

70 channels in 3 batches of ~25. This is a cost/depth trade-off — not a fundamental constraint. Batch size can change without affecting the enrichment schema or anti-pattern detection.
