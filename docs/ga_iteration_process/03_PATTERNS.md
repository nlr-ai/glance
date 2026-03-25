# Patterns — GA Iteration Process

## P1: Graph as diagnostic instrument

The L3 graph produced by Gemini Vision is the primary diagnostic artifact — not the scores alone. Node properties (weight, stability, energy) encode design state:

- **High energy** (e > 0.7) = element is unresolved, needs visual anchoring
- **Low stability** (s < 0.6) = encoding is ambiguous, needs clearer channel
- **Low weight** (w < 0.3) = element is invisible, needs size/contrast increase or removal

The graph IS the X-ray. Scores are the summary; the graph is the detail.

## P2: One archetype diagnosis, multiple targeted fixes

Each iteration starts with an archetype classification that gives the overall diagnosis. The recommendations then pinpoint specific nodes and channels to fix. The archetype tells you WHAT is wrong; the recommendations tell you WHERE and HOW.

```
Archetype (macro) --> Recommendations (micro) --> Targeted fixes (action)
```

Never fix "the archetype". Fix the specific nodes and channels that produce the archetype signature.

## P3: Convergence by energy reduction

The iteration loop converges when all node energies drop below 0.50. Energy in the GLANCE graph represents unresolved visual attention — elements that grab the eye without conveying information, or elements that need design work. Each iteration should reduce the maximum energy in the graph.

```
V1: max_energy = 0.85  (Spectacle)
V2: max_energy = 0.62  (fixes applied)
V3: max_energy = 0.41  (Cristallin)
```

If energy increases between versions, the fix introduced a new unresolved element. Roll back.

## P4: Channel upgrade paths as fix vocabulary

Fixes are not arbitrary. The recommender maps each problematic encoding to a specific upgrade path grounded in psychophysics (Cleveland & McGill, Stevens' power law):

- area -> length (Stevens beta: 0.7 -> 1.0)
- volume -> length (Stevens beta: 0.6 -> 1.0)
- color_saturation -> luminance
- color_hue alone -> length + color_hue (redundant encoding)

These are the verbs of the iteration process. The graph tells you the nouns (which elements); the upgrade paths tell you the verbs (how to fix them).

## P5: Version-tracked comparison

Every iteration produces a snapshot that is comparable to the previous version. The comparison is both visual (thumbnail side-by-side) and quantitative (delta table on all tracked metrics). No iteration happens without a clear before/after.

```
V(n) image + graph + archetype + metrics
       |
       | delta table
       v
V(n+1) image + graph + archetype + metrics
```

## P6: Fail fast on Fantome

If the initial analysis produces a Fantome archetype (nothing works — low S10, low S9b, low S2), the recommendation is a complete redesign, not incremental fixes. The iteration loop is for refinement, not resurrection. A Fantome needs a new starting point.
