# Algorithm — GA Iteration Process

Step-by-step iteration logic. Each step has a defined input, output, and failure mode.

## A1: Full iteration loop

```
Step 1: Generate or modify GA
    Input:  YAML config (parametric compositor) OR direct SVG source
    Output: SVG -> PNG (full resolution + delivery resolution)
    Tool:   compose_paper_ga.py or equivalent compositor
    Fail:   SVG render fails -> fix compositor, do not proceed

Step 2: Analyze with Gemini Vision (stratified 4-step extraction)
    Input:  PNG image bytes + filename
    Output: L3 graph YAML (space/narrative/thing nodes, typed links, metadata) saved to data/
    Tool:   vision_scorer.analyze_ga_image(image_bytes, filename)
    Process:
        2a. Gemini identifies zones → space nodes (bounded visual containers)
        2b. Gemini identifies messages → narrative nodes (intended reader effects)
        2c. Gemini identifies elements → thing nodes (bars, icons, text, shapes)
        2d. Gemini creates typed links:
            - thing → narrative ("carries" — this element carries this message)
            - thing → space ("lives_in" — this element lives in this zone)
            - narrative → space ("communicated_in" — this message is in this zone)
            - thing → thing (visual relationships: proximity, alignment, etc.)
    Fail:   Gemini API error -> retry once, then abort
    Fail:   YAML parse error -> truncation recovery in _parse_gemini_yaml()

Step 3: Classify archetype
    Input:  metadata dict from Step 2
    Output: archetype key + confidence + approximated scores
    Tool:   archetype.classify_from_vision_metadata(metadata)
    Fail:   classify returns fantome with low confidence -> flag for redesign (P6)

Step 4: Reader simulation + recommendations
    Input:  L3 graph YAML path from Step 2
    Output: reader simulation results + prioritized recommendations + accessibility warnings
    Tool:   recommender.analyze_ga(graph_path)
    Process:
        4a. Reader simulation: a virtual actor traverses space nodes in Z-pattern
            (top-left → top-right → bottom-left → bottom-right)
            - Time per space proportional to space weight
            - Attention propagates: actor → things in space → narratives linked to those things
            - Each narrative accumulates received_attention from its carrier elements
        4b. Compute simulation metrics:
            - received_attention per narrative — did the message get enough energy?
            - diversity — are narratives spread across spaces or clustered?
            - route_exists per narrative — can the Z-pattern reader reach it?
        4c. Generate recommendations based on simulation + graph diagnostics
    Fail:   Empty recommendations -> GA may already be optimal, check convergence

Step 5: Check convergence
    Conditions (ALL must be True):
        - archetype == "cristallin"
        - metadata.hierarchy_clear == True
        - metadata.word_count <= 30
        - all narratives reachable (route_exists == True for all)
        - min(narrative.received_attention) > 0.20
        - len(metadata.accessibility_issues) == 0

    If CONVERGED: exit loop, report final metrics
    If NOT CONVERGED: continue to Step 6

Step 6: Interpret recommendations and select fixes
    Input:  recommendations from Step 4 (now informed by reader simulation)
    Output: 1-2 targeted fixes to apply
    Rules:
        - Fix unreachable narratives first (route_exists == False)
        - Then fix low-attention narratives (received_attention < 0.20)
        - Then fix CRITICAL priority, then HIGH
        - Apply at most 2 fixes per iteration (avoid cascading side effects)
        - For each fix, identify: which node (space/narrative/thing), which link to add/strengthen

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
            s10_approx, archetype, min_narrative_attention,
            narrative_diversity, all_routes_exist,
            accessibility_count, space_count, narrative_count,
            thing_count, link_count]:
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

## A1b: Auto-Improve Prompt Generation

When generating improvement prompts for Gemini after reader simulation, follow the FACT → PROBLEM → QUESTION structure:

```
Step 1: FACT — specific diagnosis with node names and actual values
    Example: "narrative:key_finding has received_attention=0.12,
              carried by only thing:small_label (weight=0.2) in space:bottom_zone"

Step 2: PROBLEM — dynamic problem description derived from graph data
    Example: "The key finding is nearly invisible because its single carrier
              is a low-weight text label in the last zone of the Z-pattern.
              The reader's attention is exhausted by the time they reach it."

Step 3: QUESTION — open question for Gemini to explore
    Example: "How can we increase the key finding's visibility
              without adding visual clutter to the already-dense top zone?"
```

Each auto-improve prompt references real node IDs, real values, and real graph topology. No generic advice.

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
