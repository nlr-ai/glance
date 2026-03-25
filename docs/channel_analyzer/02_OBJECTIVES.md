# Objectives — Channel Analyzer

## Goal
Enrich a GA's L3 knowledge graph with per-node visual channel annotations, answering: "HOW does each piece of information reach the viewer's brain?"

## Non-goals
- **Not a scorer.** The channel analyzer doesn't produce a single score. It produces a map.
- **Not a replacement for GLANCE testing.** Channels predict transmission quality, but only human testing measures actual comprehension.
- **Not automated redesign.** It tells you what's wrong, not how to fix it (the recommender does that).

## Trade-offs
- **Depth vs cost:** 70 channels × Gemini call = expensive. Batching 25 at a time balances depth and API cost (3 calls per GA).
- **Precision vs recall:** Gemini may miss subtle channel usage or hallucinate channel roles. The enriched graph is a hypothesis, not ground truth.
