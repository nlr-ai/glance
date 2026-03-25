# r/bioinformatics Response Template

## Context
Bioinformatics researchers sharing papers, tools, and analyses.
This sub is primarily an INGESTION source (extracting GAs from linked papers),
but reaction is possible when GA quality is discussed.

## Tone
- Technical, data-oriented
- Bioinformatics-specific examples (heatmaps, pathway diagrams, genome browsers)
- GLANCE as a quantitative tool for a quantitative community

## Template

---

Interesting paper. We've been benchmarking graphical abstracts across domains using [GLANCE](https://glance.scisense.fr) — a framework that measures whether a GA communicates its key finding in 5 seconds.

{context_specific_paragraph}

Bioinformatics GAs have specific challenges:
- **Heatmaps**: color gradients are perceptually compressed (Stevens' beta ~0.7 for area) — readers underestimate differences
- **Pathway diagrams**: node-link structures work well for topology but poorly for quantitative comparisons
- **Multi-panel**: common in -omics, but >4 panels in a GA exceeds working memory capacity

{analysis_if_available}

The tool is free — might be useful for pre-submission GA review.

---

## Variables
- `{context_specific_paragraph}` — adapted to the paper/discussion
- `{analysis_if_available}` — GLANCE diagnosis if we extracted and scored the GA

## Rules
- NEVER post automatically — human reviews and posts manually
- Technical register — this audience knows their stats
- Specific to bioinformatics visualization challenges
- Keep under 250 words
