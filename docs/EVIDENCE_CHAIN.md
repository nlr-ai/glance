# GLANCE Premier Regard -- Evidence Chain (Validation Ladder)

## Purpose

This document defines the hierarchical chain of evidence that GLANCE must establish, from the most basic proof (the test measures something real) to the strongest claim (GLANCE is a generalizable standard). Each level builds on the previous one. If a level fails, everything above it collapses.

The evidence chain is the validation backbone for the entire GLANCE platform. It maps directly to the Guarantee Loop: each level defines RESULTS (what we prove), VALIDATION (the invariants that must hold), and the ALGORITHM (the sequence in which evidence accumulates).

**Related docs:**
- `METRICS.md` -- metric definitions and formulas
- `ARCHITECTURE.md` -- system diagram, data flow, guarantee loop
- `PIPELINE.md` -- how GAs enter the test library
- `S2b_Mathematics.md` -- mathematical model and statistical tests

---

## Level 0 -- The Test Works

The most basic requirement: the protocol measures *something* real, not noise.

| Metric | Proof | Threshold | N required |
|--------|-------|-----------|------------|
| S9b inter-GA variance | Not all GAs score ~50% | sigma > 0.15 | 5 GAs x 5 testers |
| S9b > chance | 4AFC -> chance = 25% | mean S9b > 35% | 20 tests |
| Test-retest reliability | Same person, same GA, 1 week later -> similar score | r > 0.70 | 10 pairs |

**What this proves:** the protocol measures something real, not noise.

**Gate:** if Level 0 fails (no variance), all testing stops.

---

## Level 1 -- The Test Measures Comprehension

S9b measures perceptual comprehension, not chance or general knowledge.

| Metric | Proof | What it shows |
|--------|-------|---------------|
| S9b(bar) > S9b(pie) same data | Stevens beta validated empirically | The test detects perceptual distortions |
| S9a_raw correlates with S9b | Subject recall predicts hierarchy identification | Both metrics converge |
| RT2 x S9b (speed-accuracy) | Fast & Right > Slow & Right | The test measures fluency, not just accuracy |
| Fluency(VEC) > Fluency(control) | Parametric design produces faster AND more accurate responses | GLMM > binary McNemar |

**What this proves:** S9b measures perceptual comprehension, not chance or domain expertise.

---

## Level 2 -- Stream Mode Is Valid

The ecological exposure mode (simulated scroll feed) produces valid measurements.

| Metric | Proof | What it shows |
|--------|-------|---------------|
| S10 > 0.33 (chance) | GA captures attention in a feed | Saillance is measurable |
| S10 x S9b > 0.56 | Full chain: seen AND understood | The complete attention-to-comprehension chain holds |
| S9b(stream) < S9b(spotlight) | Context reduces comprehension | Spotlight overestimates -- stream is ecological |
| Delta_spoiler < 0.10 | S9b(title) ~ S9b(nude) | The GA carries the information alone, not the title |
| Dwell time correlates with S9b | Longer viewing -> better comprehension | Beta_8 significant in regression |

**What this proves:** stream mode simulates reality and the GA survives noise.

---

## Level 3 -- Scoring Explains WHY

The model is explainable -- every failure has an identifiable, correctable cause.

| Metric | Proof | What it shows |
|--------|-------|---------------|
| Channel coverage correlates with S9b | Coverage 0.85 -> S9b ~80%. Coverage 0.50 -> S9b ~40% | Visual channel predicts comprehension |
| area encoding -> lower S9b than length | Stevens beta measured in our data | Psychophysics holds in real conditions |
| Rejection reason correlates with channel gaps | "too small" -> channel:small_details low | Rejection autopsy validates scoring |
| filter_ratio (voice) correlates with S9b | High cognitive effort -> weak design even if answer correct | Effortless accuracy is the true metric |

**What this proves:** the model is explainable -- each failure has an identifiable and correctable cause.

---

## Level 4 -- Recommendations Work

GLANCE does not just measure -- it improves.

| Metric | Proof | What it shows |
|--------|-------|---------------|
| GA V1 -> reco "area->length" -> GA V2 -> Delta_S9b > +20% | Upgrade path produces predicted improvement | Recommendations are actionable |
| Immunomod V10(VEC) vs V10(area control) | Delta_S9b > 0.30 | Our design beats the standard |
| Client GA before/after audit | S9b increases after corrections | The audit product has measurable ROI |
| Multi-domain: med + tech + climate | Recommendations work everywhere | Not a niche tool |

**What this proves:** GLANCE does not just measure -- it improves.

---

## Level 5 -- The Model Generalizes

GLANCE is a standard, not an ad-hoc tool.

| Metric | Proof | What it shows |
|--------|-------|---------------|
| H1: S9b ~ constant across quadrants | Design compensates for expertise differences | Universality |
| H5: S9a(voice) > S9a(text) | Voice captures recall better | Production bottleneck confirmed |
| Beta_5 significant in regression | ga_version predicts S9b controlled for profile | Design makes the difference, not the tester |
| 15 domains tested | Same protocol, same metrics, comparable results | Domain-agnostic |

**What this proves:** GLANCE is a standard, not an ad-hoc tool.

---

## Temporal Sequence

```
Week 1:   Level 0 (N=10)     -> "it discriminates"
Week 2:   Level 1 (N=20)     -> "it measures comprehension"
Week 3:   Level 2 (N=30)     -> "it works in a real feed"
Month 2:  Level 3 (N=50)     -> "it explains why"
Month 3:  Level 4 (N=80)     -> "it improves GAs"
Month 6:  Level 5 (N=500)    -> "it's a standard"
```

Each level builds on the previous. If Level 0 fails (no variance), everything stops.

---

## Key Metric

`channel_coverage -> S9b` (correlation)

If GAs with high channel coverage scores have high S9b, the entire model is validated -- psychophysics predicts measured comprehension.

---

## Validation Invariants

These invariants must hold across all levels. If any breaks, the corresponding level and everything above it is invalidated.

| Invariant | Level | Check |
|-----------|-------|-------|
| S9b variance sigma > 0.15 across GAs | 0 | `analytics.py` per-image stats |
| Mean S9b > 0.35 (above 4AFC chance) | 0 | Dashboard global stats |
| Test-retest r > 0.70 | 0 | Manual paired analysis |
| S9b(bar) > S9b(pie) for same data | 1 | `compute_ab_delta()` |
| S10 > 0.33 in stream mode | 2 | `compute_s10_rate()` |
| S10 x S9b > 0.56 | 2 | `compute_s10_rate()` s10_x_s9b |
| Delta_spoiler < 0.10 | 2 | Requires `stimulus_condition` implementation |
| Channel coverage correlates with S9b | 3 | Post-hoc regression analysis |
| Delta_S9b > +0.20 after recommendation | 4 | Before/after paired comparison |
| S9b ~ constant across profile quadrants | 5 | `compute_stats_by_quadrant()` chi-squared |

---

## Current Status

| Level | Status | Blocking on |
|-------|--------|-------------|
| 0 | NOT STARTED | First N=10 crash test participants |
| 1 | NOT STARTED | Level 0 completion |
| 2 | NOT STARTED | Level 1 completion + stream mode testing |
| 3 | NOT STARTED | Level 2 completion + channel coverage data |
| 4 | NOT STARTED | Level 3 completion + recommendation loop |
| 5 | NOT STARTED | Level 4 completion + N=500 participants |

---

*Evidence chain formalized 25 March 2026*
*SciSense x Mind Protocol*
