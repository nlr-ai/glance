# Behaviors — GA Iteration Process

Observable system effects. What the iteration loop does.

## B1: Vision analysis

Given a GA image (SVG rendered to PNG), the process sends it to Gemini Pro Vision with a structured YAML prompt. The model returns 5-15 nodes with weight/stability/energy, links between elements, and metadata (chart_type, word_count, hierarchy_clear, accessibility_issues, executive_summary_fr).

**Input:** PNG image bytes + filename
**Output:** Validated L3 graph YAML + raw response, saved to `data/`
**Implements:** P1 (graph as diagnostic), R2, R3

## B2: Archetype classification

The metadata from vision analysis is fed to the archetype classifier, which approximates GLANCE scores (S10, S9b, drift, warp) from structural properties (word_count, hierarchy_clear, chart_type) and classifies into one of 7 archetypes.

**Input:** Vision metadata dict
**Output:** Archetype key + confidence + approximated scores
**Implements:** P2 (one diagnosis, multiple fixes), R1

## B3: Recommendation generation

The saved L3 graph is analyzed node-by-node. High-energy nodes get design iteration flags. High-weight low-stability nodes get empirical validation flags. Accessibility checks are run. Channel upgrade paths are surfaced.

**Input:** L3 graph YAML path
**Output:** Prioritized recommendation list + strengths + accessibility warnings + upgrade paths
**Implements:** P4 (channel upgrade vocabulary), R4

## B4: Fix application

The human or AI compositor reads the recommendations and applies 1-2 targeted fixes to the GA source (YAML config for parametric compositor, or direct SVG edits). The fix vocabulary comes from the channel upgrade paths and the node-specific diagnostics.

**Input:** Recommendations + current GA source
**Output:** Modified GA source, re-rendered SVG -> PNG
**Implements:** P3 (convergence by energy reduction)

## B5: Version comparison

After re-rendering and re-analyzing, the process generates a delta table comparing V(n) and V(n+1) on all tracked metrics: hierarchy_clear, word_count, S9b approx, S10 approx, archetype, max node energy, accessibility issues, node count, link count.

**Input:** Two consecutive version analyses
**Output:** Delta table (metric, V(n) value, V(n+1) value, direction)
**Implements:** P5 (version-tracked comparison), R5

## B6: Convergence check

After the version comparison, the process checks whether convergence criteria are met: Cristallin archetype, hierarchy_clear = True, word_count <= 30, max energy < 0.50, no accessibility issues. If met, the iteration loop terminates. If not, the next iteration begins at B1.

**Input:** Delta table + current version metrics
**Output:** CONVERGED or CONTINUE + remaining gap summary
**Implements:** R1, R2, R3, R4
