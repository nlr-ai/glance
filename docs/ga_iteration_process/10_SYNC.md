# Sync — GA Iteration Process

## Current state: 25 mars 2026

### Phase: OPERATIONAL (manual workflow) — unified runner NOT YET BUILT

### What exists

The 4 core pipeline components are implemented and functional:

| Component | File | Status |
|-----------|------|--------|
| Vision scorer | `glance/vision_scorer.py` | Running — Gemini 2.5 Pro, structured YAML output, L3 graph save |
| Archetype classifier | `glance/archetype.py` | Running — 7 archetypes, rule-based + distance fallback, vision metadata approximation |
| Recommender | `glance/recommender.py` | Running — node-level diagnostics, channel upgrade paths, accessibility checks, plain-text French |
| Compositor | `glance/ga_paper/compose_paper_ga.py` | Running — parametric SVG from YAML config, two-zone architecture |

The iteration loop has been executed manually on the GLANCE paper GA (compose_paper_ga.py) across multiple versions.

### What works

- Full analysis flow: image -> Gemini Vision -> L3 graph -> archetype -> recommendations
- Archetype classification from vision metadata (approximated scores)
- Plain-language French recommendations via `get_plain_text()`
- Markdown report generation via `generate_report()`
- Parametric GA re-rendering from modified YAML config
- YAML parse recovery (handles malformed Gemini output)

### What's missing

| Item | Status | Blocker |
|------|--------|---------|
| `iterate_ga.py` (unified runner) | NOT STARTED | Manual orchestration works but is error-prone |
| `compare_versions()` function | NOT STARTED | Delta tables computed manually |
| Iteration log per GA | NOT STARTED | No structured version history storage |
| Automated regression detection | NOT STARTED | Depends on compare_versions() |
| Standalone energy checker | NOT STARTED | Energy inspected manually from graph YAML |
| Archetype convergence tracker | NOT STARTED | Archetype sequence not logged automatically |

### Relationship to GLANCE platform

This process module documents the feedback loop that connects GLANCE's diagnostic output (scores, archetypes, recommendations) to its prescriptive output (design improvement). It sits between:

- **Upstream:** vision_scorer.py (analysis), archetype.py (classification), recommender.py (recommendations)
- **Downstream:** compose_paper_ga.py (re-rendering), the GLANCE blog (iteration case studies)

### Convergence targets

| Metric | Target | Source |
|--------|--------|--------|
| Archetype | Cristallin | archetype.py |
| hierarchy_clear | True | vision_scorer metadata |
| word_count | <= 30 | vision_scorer metadata |
| S9b approx | >= 0.80 | archetype approximated scores |
| S10 approx | >= 0.60 | archetype approximated scores |
| Max node energy | < 0.50 | L3 graph nodes |
| Accessibility issues | 0 | vision_scorer metadata |
| Node count | 8-12 | L3 graph |
| Link count | >= nodes - 2 | L3 graph |

### Handoff

1. This doc chain (`docs/ga_iteration_process/`) for process documentation
2. `docs/GA_ITERATION_PROCESS.md` — predecessor monolithic document
3. `glance/vision_scorer.py` — vision analysis entry point
4. `glance/archetype.py` — classification logic
5. `glance/recommender.py` — recommendation engine
6. `glance/ga_paper/compose_paper_ga.py` — parametric compositor
7. `glance/data/` — saved L3 graphs and raw Gemini responses

### History

| Date | Action |
|------|--------|
| 2026-03-25 | GA Iteration Process documented as monolithic doc (GA_ITERATION_PROCESS.md) |
| 2026-03-25 | Doc chain conversion: 10-facet module format created (docs/ga_iteration_process/) |
