# Results — GA Iteration Process

5 measurable outcomes. Mapping 1:1 with HEALTH checkers.

## R1: Archetype convergence — reach Cristallin within 3 iterations

The GA's archetype classification shifts from its initial diagnosis (Spectacle, Encyclopedie, Fantome, etc.) to Cristallin across successive iterations. Each iteration should reduce distance to the Cristallin profile.

**Sense:** Archetype key per version. Track archetype sequence across versions.
**Health:** CH1 (archetype classification runs successfully each version)
**Carrier:** Silas

## R2: Hierarchy clarity — hierarchy_clear = True

The GA's visual hierarchy communicates which result is most important within 5 seconds. Gemini Vision's `hierarchy_clear` metadata field must be `True`.

**Sense:** `metadata.hierarchy_clear` from vision_scorer output.
**Health:** CH2 (hierarchy_clear flips from False to True across iterations)
**Carrier:** Silas

## R3: Text parsimony — word_count <= 30

The GA contains at most 30 visible words. Every word beyond 30 activates System 2 processing and increases decode time beyond the 5-second scroll budget.

**Sense:** `metadata.word_count` from vision_scorer output.
**Health:** CH3 (word_count <= 30 in final version)
**Carrier:** Silas

## R4: Energy resolution — all node energies < 0.50

Every node in the L3 graph has energy below 0.50, meaning all visual elements are settled and finalized. High-energy nodes indicate unresolved design decisions.

**Sense:** `max(node.energy for node in graph.nodes)` per version.
**Health:** CH4 (max energy check per version)
**Carrier:** Silas

## R5: Monotonic improvement — no regression between versions

Each iteration V(n) -> V(n+1) improves or holds on at least one tracked metric without regressing any metric beyond tolerance (5% margin). The process converges; it does not oscillate.

**Sense:** Delta table comparing V(n) vs V(n+1) on all tracked metrics.
**Health:** CH5 (delta table generated and no regressions detected)
**Carrier:** Silas

## Guarantee Loop

```
R1 (archetype)   <- CH1 (archetype classified each version)  <- S_CH1 (classify_from_vision_metadata succeeds)
R2 (hierarchy)   <- CH2 (hierarchy_clear tracked)             <- S_CH2 (metadata.hierarchy_clear field present)
R3 (parsimony)   <- CH3 (word_count check)                    <- S_CH3 (metadata.word_count <= 30)
R4 (energy)      <- CH4 (max node energy check)               <- S_CH4 (max(energy) < 0.50)
R5 (monotonic)   <- CH5 (delta table, no regression)          <- S_CH5 (version comparison computed)
```
