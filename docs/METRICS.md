# GLANCE Premier Regard -- Metrics Reference

All metrics computed by the GLANCE platform, in one place. For mathematical derivations and justifications, see `S2b_Mathematics.md`.

---

## Metric Chain — WHAT / WHO / HOW MUCH Sequential Gates

The brain processes a GA in three sequential gates (P0 Context Anchor insight, 2026-03-26):

1. **WHAT** — Domain identification (<1s). Needs title + illustration. Measured by **S9a** + **S9context**.
2. **WHO** — Agent/product identification (1-3s). Needs labeled elements. Measured by **S9b**.
3. **HOW MUCH** — Evidence hierarchy (3-5s). Needs proportional encoding. Measured by **S9b** (rank order) + **S9c** (actionability).

Each gate is prerequisite: if WHAT fails, WHO is noise; if WHO fails, HOW MUCH is random.

```
S10 ---------> S9a ---------> S9context ---------> S9b ---------> S9c
(saillance)    (recall)       (narrative           (hierarchy)    (actionability)
"I saw it"     "I know what    anchoring)          "I know which  "I would change
                it is"         "I know WHY          is best"       my practice"
                                it matters"
               ╰─── WHAT ───╯                     ╰── WHO+HOW MUCH ──╯
```

S10 is measured only in stream mode. S9a/S9context/S9b/S9c are measured in both modes. The full chain must hold for a GA to produce clinical impact. S9context is the bridge between domain recognition (WHAT) and hierarchy decoding (WHO/HOW MUCH) — without narrative anchoring, hierarchy is perceived without meaning.

---

## Primary Scores

### S9a -- Reconnaissance Semantique (Subject Identification)

| Property | Value |
|----------|-------|
| **Question** | Q1: "Que venez-vous de voir ?" (free recall) |
| **Formula** | `S9a = 1 if max(cos_sim(embed(q1_text), embed(ref_i))) >= 0.40, else 0` |
| **Range** | Binary: 0 or 1 |
| **Continuous score** | `s9a_score`: float in [0.0, 1.0] (max cosine similarity) |
| **Threshold** | 0.40 (config: `s9a_pass_threshold`) |
| **Computed in** | `semantic.py:score_s9a_semantic()` |
| **Stored in DB** | `tests.s9a_pass` (int), `tests.s9a_score` (real) |
| **Aggregate** | `Taux_S9a = sum(S9a) / N` |
| **Target** | Taux_S9a >= 0.60 |
| **Math ref** | S2b_Mathematics.md section 2 |

The continuous `s9a_score` is preserved for post-hoc threshold tuning. The model is `paraphrase-multilingual-mpnet-base-v2` (278M params, 768-dim embeddings). References are multi-level (L1 broad, L2 specific, L3 detailed) and cached in memory per GA version.

### S9context -- Ancrage Narratif (Narrative Context Anchoring)

| Property | Value |
|----------|-------|
| **Question** | Q1b: "Pourquoi cette information est-elle importante ?" (free recall, follows Q1) |
| **Formula** | `S9context = 1 if max(cos_sim(embed(q1b_text), embed(narrative_ref_i))) >= 0.35, else 0` |
| **Range** | Binary: 0 or 1 |
| **Continuous score** | `s9context_score`: float in [0.0, 1.0] (max cosine similarity) |
| **Threshold** | 0.35 (config: `s9context_pass_threshold`) — lower than S9a because narrative anchoring is more abstract |
| **Computed in** | `semantic.py:score_s9context()` (planned) |
| **Stored in DB** | `tests.s9context_pass` (int), `tests.s9context_score` (real) |
| **Aggregate** | `Taux_S9context = sum(S9context) / N` |
| **Target** | Taux_S9context >= 0.50 |
| **Source** | P0 Context Anchor insight (2026-03-26) |

**Rationale:** S9a measures WHAT domain ("immunology", "oncology") but not WHY the data matters. A participant who says "I saw a cancer study" (S9a pass) but cannot articulate why it matters (S9context fail) has identified the domain without anchoring. Narrative anchoring bridges WHAT and WHO — it provides the contextual frame that makes hierarchy meaningful. References are narrative nodes linked to the GA's thing nodes in the L3 graph.

**Gate dependency:** S9context is only meaningful when S9a passes. If S9a = 0, S9context is recorded but excluded from aggregate calculations (the reader didn't even identify the domain).

---

### S9b -- Hierarchie Perceptive (Hierarchy Perception)

| Property | Value |
|----------|-------|
| **Question** | Q2: "Quel produit vous a semble le mieux documente ?" (forced choice) |
| **Formula** | `S9b = 1 if q2_choice == correct_product, else 0` |
| **Range** | Binary: 0 or 1 |
| **Computed in** | `scoring.py:score_s9b()` |
| **Stored in DB** | `tests.s9b_pass` (int) |
| **Aggregate** | `Taux_S9b = sum(S9b) / N` |
| **Thresholds** | >= 0.80 PASS, 0.60-0.80 WARN, < 0.60 FAIL |
| **Math ref** | S2b_Mathematics.md section 2 |

**This is the primary metric.** It directly measures whether the GA's visual hierarchy was perceived correctly. Case-insensitive exact match. Chance level = 1/4 = 0.25 (4AFC + "Je ne sais pas" option counted as wrong).

### S9c -- Actionnabilite (Actionability)

| Property | Value |
|----------|-------|
| **Question** | Q3: "Cela modifierait-il votre prise en charge ?" (3 options) |
| **Formula** | `S9c = 1.0 if yes, 0.5 if need_more_data, 0.0 if no` |
| **Range** | Ordinal: {0.0, 0.5, 1.0} |
| **Computed in** | `scoring.py:score_s9c_graduated()` |
| **Stored in DB** | `tests.s9c_score` (real), `tests.s9c_pass` (int, backward compat) |
| **Aggregate** | `Score_S9c = sum(S9c) / N` |
| **Target** | Score_S9c >= 0.40 |
| **Math ref** | S2b_Mathematics.md section 2 |

The 0.5 for "need more data" reflects that in evidence-based medicine, asking for more evidence is rational, not a failure.

---

## Composite Score

### GLANCE -- Score Composite

| Property | Value |
|----------|-------|
| **Formula** | `GLANCE = 0.15 * S9a + 0.10 * S9context + 0.45 * S9b + 0.30 * S9c` |
| **Range** | [0.0, 1.0] |
| **Computed in** | `scoring.py:score_glance_composite()` |
| **Stored in DB** | `tests.glance_score` (real) |
| **Pass threshold** | 0.70 (config: `glance_pass_threshold`) |
| **Pass label** | "Decodage reussi" |
| **Fail label** | "Le design n'a pas survecu au transfert" |
| **Math ref** | S2b_Mathematics.md section 7 |

Weights rationale aligned with WHAT/WHO/HOW MUCH gates:
- **WHAT gate (0.25 total):** S9a at 0.15 (domain recall, noisy) + S9context at 0.10 (narrative anchoring, new). Split from original S9a=0.20, with 0.05 redistributed from S9b.
- **WHO + HOW MUCH gate (0.75 total):** S9b at 0.45 (hierarchy, primary metric, down from 0.50 to fund S9context) + S9c at 0.30 (actionability, unchanged).
- The total still sums to 1.00. S9b remains dominant. S9context captures the WHAT/WHO bridge that was previously unmeasured. This is an operational convenience for the dashboard, not a primary analysis variable.

---

## Saillance (Stream Mode Only)

### S10 -- Saillance

| Property | Value |
|----------|-------|
| **Measurement** | Participant selects the target GA from 3 thumbnails (target + 2 leurres) after the stream feed |
| **Formula** | `S10 = 1 if stream_selected_id == target_filename, else 0` |
| **Range** | Binary: 0 or 1 |
| **Computed in** | `app.py:submit_test()` (s10_hit computation) |
| **Stored in DB** | `tests.s10_hit` (int: 1=hit, 0=miss, NULL=spotlight) |
| **Aggregate** | `S10_rate = sum(s10_hit) / N_stream` |
| **Thresholds** | > 0.70 scroll-stopping validated, 0.33-0.70 not memorable, < 0.33 actively ignored |
| **Chance level** | 1/3 = 0.33 |
| **Analytics** | `analytics.py:compute_s10_rate()` |
| **Math ref** | S2b_Mathematics.md section 8 |

### S10 x S9b -- Chain Metric

| Property | Value |
|----------|-------|
| **Formula** | `S10_rate * Taux_S9b` (stream tests only) |
| **Range** | [0.0, 1.0] |
| **Computed in** | `analytics.py:compute_s10_rate()` (returned as `s10_x_s9b`) |
| **Target** | > 0.56 |
| **Math ref** | S2b_Mathematics.md section 8 |

Measures whether the full chain holds: a GA must both capture attention (S10) AND transfer correct information (S9b). A high S10 with low S9b = visual spin (attention without comprehension). A high S9b with low S10 = invisible correctness (comprehension without attention).

---

## Temporal Metrics

### RT2 -- Temps de Decision Hierarchique

| Property | Value |
|----------|-------|
| **Measurement** | `q2_time_ms`: milliseconds from Q2 appearance to participant click |
| **Aggregate** | `Mediane_RT2 = median(q2_time_ms)` |
| **Classification** | `classify_rt2()` in `scoring.py` |
| **Thresholds** | < 3000ms fluent, 3000-8000ms hesitant, > 8000ms lost |
| **Config keys** | `rt2_fast_slow_ms` (3000), `rt2_hesitant_lost_ms` (8000) |
| **Math ref** | S2b_Mathematics.md section 3 |

RT2 follows a log-normal distribution. Median is the appropriate central tendency estimator (robust to outliers).

### Speed-Accuracy Tradeoff

| Property | Value |
|----------|-------|
| **Formula** | Cross of S9b (correct/incorrect) x RT2 (fast/slow) |
| **Categories** | `fast_right`, `slow_right`, `fast_wrong`, `slow_wrong` |
| **Computed in** | `scoring.py:classify_speed_accuracy()` |
| **Stored in DB** | `tests.speed_accuracy` (text) |
| **Analytics** | `analytics.py:compute_speed_accuracy_distribution()` |
| **Math ref** | S2b_Mathematics.md section 3 |

```
                    S9b correct          S9b incorrect
                 ┌─────────────────┬──────────────────┐
  RT2 < 3000ms  │  fast_right     │  fast_wrong       │
                │  (design works) │  (design misleads) │
                ├─────────────────┼──────────────────┤
  RT2 >= 3000ms │  slow_right     │  slow_wrong        │
                │  (effort needed)│  (design fails)    │
                └─────────────────┴──────────────────┘
```

`fast_wrong` is the worst case: the design actively sends the wrong perceptual signal (visual spin).

### Keystroke Dynamics (Q1)

| Metric | Formula | File:Function | What it measures | Thresholds |
|--------|---------|---------------|------------------|------------|
| Latence d'acces | `q1_first_keystroke_ms` | (JS client, stored in DB) | Speed of memory retrieval | < 1500ms immediate, 1500-4000ms standard, > 4000ms reconstruction |
| Duree de production | `q1_last_keystroke_ms - q1_first_keystroke_ms` | (derived) | Richness of encoded memory | < 3000ms short, > 3000ms long |
| Delai de validation | `q1_time_ms - q1_last_keystroke_ms` | (derived) | Subjective confidence | < 500ms no rereading, > 3000ms rereading/hesitation |

Combined into a 2x2 matrix:

| | Short production (< 3s) | Long production (> 3s) |
|---|---|---|
| **Fast latency (< 1.5s)** | Flash: knows exactly, says it fast | Rich: knows and has a lot to say |
| **Slow latency (> 1.5s)** | Minimal: searches then summarizes in one word | Laborious: doesn't remember clearly |

"Flash" and "Rich" indicate strong GA encoding. "Laborious" correlates with low S9a.

---

## A/B Comparison Metrics

### Delta_S9b -- Correction Cognitive

| Property | Value |
|----------|-------|
| **Formula** | `Delta_S9b = Taux_S9b(VEC) - Taux_S9b(control)` |
| **Range** | [-1.0, +1.0] |
| **Computed in** | `analytics.py:compute_ab_delta()` |
| **Interpretation** | > +0.30 publishable, +0.10 to +0.30 moderate, -0.10 to +0.10 no difference, < -0.10 VEC is worse |
| **Statistical test** | McNemar chi-squared on paired data |
| **Significance** | chi2 > 3.84 => p < 0.05 |
| **Min pairs** | 10 (config: `mcnemar_min_pairs`) |
| **Math ref** | S2b_Mathematics.md section 5 |

Control images use area encoding (pie charts, bubble charts, Stevens beta ~0.7). VEC images use length encoding (bars, Stevens beta ~1.0). The delta measures the perceptual advantage of length over area.

### Delta_spoiler -- Effet du Titre

| Property | Value |
|----------|-------|
| **Formula** | `Delta_spoiler = S9b(title_only) - S9b(nude)` |
| **Target** | < +0.10 (the GA encodes information independently of the title) |
| **Status** | Planned (requires `stimulus_condition` implementation) |
| **Math ref** | S2b_Mathematics.md section 1 (4 exposure conditions) |

If Delta_spoiler is large (> +0.10), the title is carrying the information -- the GA is decorative, not informative. This is the key sales metric for VEC: proving the design works without textual context.

---

## Structural Coverage Metrics (Graph-Derived)

These metrics are computed from the L3 graph structure, not from participant responses. They measure whether the GA's design provides sufficient narrative scaffolding for the WHAT/WHO/HOW MUCH gates to function.

### narrative_coverage -- Couverture Narrative

| Property | Value |
|----------|-------|
| **Question** | For each visual element (thing node), is it linked to at least one narrative? |
| **Formula** | `narrative_coverage = count(things with >= 1 narrative link) / count(all things)` |
| **Range** | [0.0, 1.0] |
| **Target** | >= 0.90 |
| **Computed from** | L3 graph: thing nodes linked to narrative nodes via `link` edges |
| **Source** | P0 Context Anchor insight (2026-03-26) |

**Rationale:** A thing node (product, molecule, data point) without a narrative link is an orphan — the viewer sees it but has no frame for WHY it matters. Low narrative_coverage predicts low S9context scores. A GA with narrative_coverage < 0.90 has visual elements that exist outside any story, making the WHAT gate fragile.

### channel_diversity_per_narrative -- Diversite de Canal par Narratif

| Property | Value |
|----------|-------|
| **Question** | How many distinct visual channels encode each key narrative? |
| **Formula** | `channel_diversity_per_narrative = mean(count(distinct channels per narrative))` |
| **Range** | [1.0, N_channels] |
| **Target** | >= 2.0 (a narrative on 1 channel is fragile) |
| **Computed from** | L3 graph: narrative nodes, their linked thing nodes, and each thing's visual channel assignments |
| **Source** | P0 Context Anchor insight (2026-03-26) |

**Rationale:** If a narrative is carried by only one visual channel (e.g., color alone), any perceptual failure on that channel (color blindness, low contrast, screen calibration) eliminates the narrative. Redundancy across channels (color + position, size + label) makes the WHO and HOW MUCH gates robust. Target >= 2.0 means each narrative is, on average, encoded in at least two independent channels.

---

## Integrity Metrics

### Tab-Switch Invalidation

| Property | Value |
|----------|-------|
| **Measurement** | `tab_switched`: detected via `document.visibilitychange` during exposure/feed |
| **Formula** | `Taux_invalidation = sum(tab_switched) / N_total` |
| **Stored in DB** | `tests.tab_switched` (int: 0 or 1) |
| **Threshold** | < 20% normal, > 20% signals UX or engagement problem |
| **Math ref** | S2b_Mathematics.md section 3 |

Invalid tests are stored but excluded from S9a/S9b/S9c calculations. The invalidation rate itself is diagnostic.

---

## Profile Stratification

### Quadrant Classification

| Property | Value |
|----------|-------|
| **Axes** | Clinical expertise (high/low) x Data literacy (high/low) |
| **Categories** | Q1_public_naif, Q2_tech, Q3_clinicien, Q4_clinicien_chercheur |
| **Computed in** | `analytics.py:compute_profile_quadrant()` |
| **Analytics** | `analytics.py:compute_stats_by_quadrant()` |
| **Math ref** | S2b_Mathematics.md section 4 |

| | Low data literacy | High data literacy |
|---|---|---|
| **Low clinical** | Q1: Public naif | Q2: Tech |
| **High clinical** | Q3: Clinicien | Q4: Clinicien + chercheur |

H1 (universality) predicts Taux_S9b should be similar across all 4 quadrants. A significant difference (chi-squared, p < 0.05) means the VEC does not universally transfer information.

---

## Dashboard Analytics Summary

| Section | Function | Metrics shown |
|---------|----------|---------------|
| Global stats | `compute_aggregate_stats()` | Taux_S9a, Taux_S9context, Taux_S9b, Score_S9c, Mediane_RT2, RT2_class, Score_GLANCE, N |
| Speed-accuracy | `compute_speed_accuracy_distribution()` | Counts per quadrant: fast_right, slow_right, fast_wrong, slow_wrong |
| Profile quadrants | `compute_stats_by_quadrant()` | Same as global, per quadrant |
| A/B delta | `compute_ab_delta()` | delta_s9b, taux_s9b per group, mcnemar_chi2, mcnemar_significant |
| Invalidation | (inline in `app.py`) | Taux_invalidation as percentage |
| Stream vs Spotlight | `compute_aggregate_stats()` per mode | Separate stats for each exposure_mode |
| S10 saillance | `compute_s10_rate()` | s10_rate, n_stream, n_hits, s10_label, s10_x_s9b |
| Structural coverage | (graph-derived, planned) | narrative_coverage, channel_diversity_per_narrative |
