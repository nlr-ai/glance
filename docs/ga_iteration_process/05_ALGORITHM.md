# Algorithm — GA Iteration Process

Step-by-step iteration logic. Each step has a defined input, output, and failure mode.

## A1: Full iteration loop

```
Step 1: Generate or modify GA
    Input:  YAML config (parametric compositor) OR direct SVG source
    Output: SVG -> PNG (full resolution + delivery resolution)
    Tool:   compose_paper_ga.py or equivalent compositor
    Fail:   SVG render fails -> fix compositor, do not proceed

Step 2: Analyze with Gemini Vision
    Input:  PNG image bytes + filename
    Output: L3 graph YAML (nodes, links, metadata) saved to data/
    Tool:   vision_scorer.analyze_ga_image(image_bytes, filename)
    Fail:   Gemini API error -> retry once, then abort
    Fail:   YAML parse error -> truncation recovery in _parse_gemini_yaml()

Step 3: Classify archetype
    Input:  metadata dict from Step 2
    Output: archetype key + confidence + approximated scores
    Tool:   archetype.classify_from_vision_metadata(metadata)
    Fail:   classify returns fantome with low confidence -> flag for redesign (P6)

Step 4: Generate recommendations
    Input:  L3 graph YAML path from Step 2
    Output: prioritized recommendations + strengths + accessibility warnings
    Tool:   recommender.analyze_ga(graph_path)
    Fail:   Empty recommendations -> GA may already be optimal, check convergence

Step 5: Check convergence
    Conditions (ALL must be True):
        - archetype == "cristallin"
        - metadata.hierarchy_clear == True
        - metadata.word_count <= 30
        - max(node.energy for all nodes) < 0.50
        - len(metadata.accessibility_issues) == 0

    If CONVERGED: exit loop, report final metrics
    If NOT CONVERGED: continue to Step 6

Step 6: Interpret recommendations and select fixes
    Input:  recommendations from Step 4
    Output: 1-2 targeted fixes to apply
    Rules:
        - Fix CRITICAL priority first, then HIGH
        - Apply at most 2 fixes per iteration (avoid cascading side effects)
        - For each fix, identify: which node, which channel, what upgrade path

Step 7: Apply fixes to GA source
    Input:  selected fixes + GA source (YAML config or SVG)
    Output: modified GA source
    Tool:   manual edit of config YAML, or programmatic SVG modification
    Fail:   fix cannot be expressed in current compositor -> document limitation

Step 8: Re-render
    Input:  modified GA source
    Output: new SVG -> PNG (V(n+1))
    Tool:   compositor re-run

Step 9: Compare versions
    Input:  V(n) analysis + V(n+1) analysis
    Output: delta table on all tracked metrics
    Method:
        For each metric in [hierarchy_clear, word_count, s9b_approx,
            s10_approx, archetype, max_energy, accessibility_count,
            node_count, link_count]:
            delta = V(n+1).metric - V(n).metric
            direction = improved / regressed / unchanged
    Fail:   Any regression > 5% -> flag as warning, review fix

Step 10: Log iteration
    Input:  delta table + archetype + recommendations applied
    Output: iteration record (version number, date, changes, metrics)
    Storage: appended to iteration log for the GA

Step 11: Loop
    Return to Step 2 with V(n+1) as the new input
    Max iterations: 5 (if not converged after 5, escalate to redesign)
```

## A2: First-time analysis (no prior version)

```
Step 1: Obtain GA image (any format)
Step 2: Run through vision_scorer (Step 2 of A1)
Step 3: Classify archetype (Step 3 of A1)
Step 4: Generate recommendations (Step 4 of A1)
Step 5: Report initial diagnosis + recommended first fixes
        No delta table (no prior version to compare)
```

## A3: Blog display format per iteration

```
For each version V(n):
    - Thumbnail of the GA image
    - Archetype badge (emoji + name_fr + color)
    - Score summary (S9b approx, S10 approx, word_count)
    - Delta table vs V(n-1) (if n > 1)
    - Key recommendation that drove the next iteration
```
