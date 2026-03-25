# Health — GA Iteration Process

5 health checkers mapping to 5 results. 1 RESULT = 1 MEASUREMENT.

```
R1 (archetype convergence) <- CH1 (archetype classified)      <- S_CH1 (classify succeeds)
R2 (hierarchy clarity)     <- CH2 (hierarchy_clear tracked)    <- S_CH2 (field present in metadata)
R3 (text parsimony)        <- CH3 (word_count check)           <- S_CH3 (word_count <= 30)
R4 (energy resolution)     <- CH4 (max energy check)           <- S_CH4 (max(energy) < 0.50)
R5 (monotonic improvement) <- CH5 (delta table, no regression) <- S_CH5 (comparison computed)
```

---

## CH1: Archetype classified each version -> validates R1

Every analyzed GA version produces an archetype classification with a confidence score.

### Sense signals

| ID | Signal | Checks | Automation |
|----|--------|--------|------------|
| S_CH1a | Archetype key present | `result["archetype"]` is a valid key in ARCHETYPES dict | Auto — key lookup |
| S_CH1b | Confidence > 0.05 | `result["confidence"] > 0.05` | Auto — bound check |
| S_CH1c | Method recorded | `result["method"]` is one of "rule", "distance", "vision_approximation" | Auto — enum check |

**Checker:** Post-analysis assertion in the iteration loop.

**Carrier:** Silas.

**Status:** Closed — archetype.py always returns a classification (distance fallback guarantees non-null).

---

## CH2: hierarchy_clear tracked -> validates R2

The hierarchy_clear field is present and tracked across versions.

### Sense signals

| ID | Signal | Checks | Automation |
|----|--------|--------|------------|
| S_CH2a | Field present | `metadata.get("hierarchy_clear")` is not None | Auto — key check |
| S_CH2b | Field is boolean | `isinstance(metadata["hierarchy_clear"], bool)` | Auto — type check |
| S_CH2c | Value tracked per version | hierarchy_clear appears in delta table | Auto — delta table generation |

**Checker:** vision_scorer._validate_graph() defaults hierarchy_clear to False if missing.

**Carrier:** Silas.

**Status:** Closed — defaulting behavior in _validate_graph() guarantees field presence.

---

## CH3: word_count <= 30 in final version -> validates R3

The final GA version has a word count at or below 30.

### Sense signals

| ID | Signal | Checks | Automation |
|----|--------|--------|------------|
| S_CH3a | word_count present | `metadata.get("word_count")` is not None | Auto — key check |
| S_CH3b | word_count is integer | `isinstance(metadata["word_count"], int)` | Auto — type check |
| S_CH3c | word_count <= 30 | `metadata["word_count"] <= 30` | Auto — bound check |

**Checker:** Convergence check in A1 Step 5.

**Carrier:** Silas.

**Status:** Partially closed — check exists in convergence criteria but not as a standalone automated checker.

---

## CH4: max node energy < 0.50 -> validates R4

The maximum energy across all nodes in the L3 graph is below 0.50.

### Sense signals

| ID | Signal | Checks | Automation |
|----|--------|--------|------------|
| S_CH4a | Nodes present | `len(graph["nodes"]) >= 3` | Auto — count check |
| S_CH4b | Energy fields valid | All `node["energy"]` values are float in [0.0, 1.0] | Auto — _validate_graph() clamps |
| S_CH4c | Max energy < 0.50 | `max(n["energy"] for n in nodes) < 0.50` | Auto — max check |

**Checker:** Convergence check in A1 Step 5.

**Carrier:** Silas.

**Status:** Open — no standalone checker. Energy is inspected manually from graph YAML.

---

## CH5: Delta table, no regression -> validates R5

Every iteration (n > 1) has a delta table and no metric regresses beyond 5% tolerance.

### Sense signals

| ID | Signal | Checks | Automation |
|----|--------|--------|------------|
| S_CH5a | Delta table exists | Comparison between V(n) and V(n+1) is computed | Manual — no compare_versions() yet |
| S_CH5b | No regression > 5% | All metric deltas are >= -0.05 (5% tolerance) | Manual — visual inspection |
| S_CH5c | At least one improvement | At least one metric strictly improved | Manual — visual inspection |

**Checker:** Not yet implemented.

**Carrier:** Silas.

**Status:** Open — delta table generation and regression checking are manual. Need `compare_versions()` function.

---

## Open loops

| Loop | Missing link | What's needed | Who |
|------|-------------|---------------|-----|
| CH4 | Standalone energy checker | Script that reads graph YAML and asserts max(energy) < 0.50 | Silas |
| CH5 | compare_versions() | Function to compute delta table between two version analyses | Silas |
| CH5 | Automated regression detection | Assert no metric regresses > 5% | Silas |
| All | Unified iteration runner | `iterate_ga.py` that chains Steps 2-10 of A1 automatically | Silas |
| R1 | Archetype convergence tracking | Log archetype sequence across versions, flag if not converging | Silas |
