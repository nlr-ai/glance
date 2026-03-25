# Validation — GA Iteration Process

## Invariants (MUST)

**IV1: Every version must have a graph.** Every GA version submitted to the iteration loop MUST produce a valid L3 graph with at least 3 nodes and metadata. A version without a graph is unanalyzed. Health: CH1. Supports R1, R2, R3, R4.

**IV2: Every version must have an archetype.** The archetype classifier MUST produce a classification for every analyzed version. Classification may be rule-based or distance-based, but never absent. Health: CH1. Supports R1.

**IV3: Metadata completeness.** The vision analysis metadata MUST contain at minimum: `hierarchy_clear` (bool), `word_count` (int), `chart_type` (str), `accessibility_issues` (list). Missing fields default to conservative values (hierarchy_clear=False, word_count=999). Health: CH2, CH3. Supports R2, R3.

**IV4: Node property bounds.** Every node in the L3 graph MUST have weight, stability, and energy clamped to [0.0, 1.0]. Out-of-range values are clamped by `_validate_graph()` in vision_scorer.py. Health: CH4. Supports R4.

**IV5: Delta table for every iteration (n > 1).** Every version V(n+1) where n >= 1 MUST have a delta table comparing it to V(n). No blind iteration — every fix must be measured. Health: CH5. Supports R5.

## Invariants (NEVER)

**IVN1: NEVER skip analysis after a fix.** Every fix applied to the GA source MUST be followed by a full re-analysis (Gemini Vision + archetype + recommender). Fixes without re-analysis are unverified design changes.

**IVN2: NEVER apply more than 2 fixes per iteration.** Applying too many changes simultaneously makes it impossible to attribute improvement or regression to specific fixes. If 5 things need fixing, do 3 iterations, not 1.

**IVN3: NEVER continue past 5 iterations without escalation.** If the GA has not converged to Cristallin after 5 iterations, the problem is structural, not incremental. Escalate to redesign (P6).

## Invariants (PROCESS)

**IV6: Recommendation traceability.** Each fix applied MUST reference the specific recommendation (node ID + issue) that motivated it. This enables post-hoc analysis of which recommendation types are most effective.

**IV7: Image preservation.** Every version's PNG MUST be preserved alongside its graph YAML. The iteration history is meaningless without the visual artifacts. Stored in `data/` alongside the graph files.
