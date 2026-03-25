# Objectives — GA Iteration Process

## O1: Goal

Transform any GA from its initial archetype into a Cristallin GA through a structured feedback loop: analyze with Gemini Vision, classify the archetype, generate graph-based recommendations, apply targeted fixes, and re-analyze. Delivers R1-R5.

The process is the bridge between GLANCE's diagnostic capability (scoring) and its prescriptive capability (design improvement). Without iteration, GLANCE is a thermometer; with it, GLANCE is medicine.

## Non-Goals

- **NO1: Not an automated redesign tool.** The process generates recommendations and diagnostics. A human or AI compositor applies the fixes. The loop is human-in-the-loop, not fully autonomous.
- **NO2: Not a single-pass optimizer.** The process is explicitly iterative. Attempting to fix everything in one pass produces side effects (fixing hierarchy can break word count). One or two targeted fixes per iteration.
- **NO3: Not a general image editor.** The process works on Graphical Abstracts analyzed through the GLANCE vision pipeline. It does not handle arbitrary image improvement.
- **NO4: Not a replacement for user testing.** Vision-based archetype classification is an approximation (method="vision_approximation"). True S9a/S9b/S9c scores require real user tests. The iteration process prepares a GA for testing; it does not replace it.

## Tradeoffs

- **T1: Speed vs. thoroughness.** Each iteration requires a Gemini Vision API call (~5-15s, ~$0.01-0.03). Rapid iteration is possible but not free. Target: converge in 2-4 iterations, not 10.
- **T2: Approximated scores vs. empirical scores.** The archetype classifier uses vision metadata approximations (S10, S9b, drift, warp are estimated, not measured). Recommendations may over- or under-correct. This is acceptable for pre-test design iteration.
- **T3: Targeted fixes vs. global redesign.** The process favors incremental targeted fixes (1-2 per iteration) over wholesale redesign. This reduces risk of regression but may take more iterations for severely broken GAs.
