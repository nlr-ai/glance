# GLANCE Premier Regard -- Architecture

## Purpose

GLANCE is a comprehension test platform that measures whether a Graphical Abstract (GA) correctly transfers its intended information hierarchy to a viewer in 5 seconds. It is the validation layer of the Visual Evidence Compiler (VEC): the VEC generates GAs, GLANCE measures whether they work.

The name "Premier Regard" (first glance) captures the design principle: if a GA's hierarchy isn't perceived in a single glance, the design has failed.

The core claim GLANCE tests: **length-encoded GAs (VEC) produce faster and more accurate hierarchy perception than area-encoded GAs (industry standard)**.

---

## Two Exposure Modes

GLANCE supports two test protocols on the same platform:

| Mode | Template | What it measures | Validity |
|------|----------|-----------------|----------|
| **Spotlight** | `test.html` | Comprehension under focused attention (ceiling) | Internal -- upper bound |
| **Stream (Flux)** | `test_flux.html` | Comprehension under ambient attention (ecological) | External -- generalizable |

**Spotlight** (original): Brief -> 3s countdown -> 5s focused exposure -> Q1/Q2/Q3/Q4. The participant knows an image is coming and prepares. This is the System 2 condition.

**Stream (Flux)** (current default): Brief -> auto-scrolling feed of 6 items (target GA + 5 leurres, 4s each) -> S10 thumbnail selection -> Q1/Q2/Q3/Q4. The participant scrolls naturally through a simulated TOC. This is the System 1 condition.

Mode switching is controlled by `config.yaml`:

```yaml
flux:
  enabled: true         # false = spotlight mode
  n_items: 6
  item_duration_ms: 4000
  target_position: random
  scroll_transition_ms: 300
```

Both modes produce the same S9a/S9b/S9c scores and store to the same DB schema. The `exposure_mode` column (`spotlight` or `stream`) tags each test. Scores from different modes must never be aggregated together.

---

## System Diagram

```
  Browser (vanilla JS)                    Server (FastAPI)
  =====================                   ================

  index.html ------GET /----------->  app.index()
                                         |
  onboard.html ---POST /onboard---->  app.onboard_submit()
                                         |  create_participant() -> SQLite
                                         |  set cookie (glance_token)
                                         v
                                     app.test_page()
                                         |  get_next_image() -> random unseen
                                         |  load domain questions from config.yaml
                                         |  check flux.enabled in config
                                         |
                              ┌───────────┴───────────┐
                              v                       v
  test.html ----GET /test---->              test_flux.html ----GET /test---->
       |  (spotlight mode)                       |  (flux/stream mode)
       |  JS: BRIEFING ->                        |  JS: BRIEFING ->
       |  COUNTDOWN -> EXPOSURE                  |  FEED (auto-scroll 6 items) ->
       |  -> Q1 -> Q2 -> Q3 -> Q4               |  SELECTION (S10 thumbnails) ->
       |                                         |  Q1 -> Q2 -> Q3 -> Q4
       |                                         |
       +--------POST /submit----------------+----+
                                             |
                                         app.submit_test()
                                             |  load sidecar JSON (semantic_references)
                                             |  score_test() -> scoring.py + semantic.py
                                             |  compute s10_hit (stream mode only)
                                             |  save_test() -> SQLite
                                             v
  reveal.html ---GET /reveal/{id}--> app.reveal()
                                         |  get_test(), get_stats()
                                         |  compute composite + speed-accuracy
                                         v
  dashboard.html -GET /dashboard---> app.dashboard()
                                         |  get_all_tests()
                                         |  compute_aggregate_stats() (global + per-mode)
                                         |  compute_stats_by_quadrant()
                                         |  compute_speed_accuracy_distribution()
                                         |  compute_ab_delta()
                                         |  compute_s10_rate()
                                         v

  Storage                            ga_library/
  =======                            ==========
  data/glance.db (SQLite, WAL)          *.png   (47 GA images)
    - participants                   *.json  (47 sidecar metadata + semantic_references)
    - ga_images                      REGISTRY.yaml (library index)
    - tests                          leurres/  (10 distractor images + leurres.json)
                                     generate_library.py (batch generator)
```

---

## File Map

| File | Role |
|------|------|
| `app.py` | FastAPI application. Routes, template rendering, image seeding, flux feed builder, form handling. ~385 lines. |
| `db.py` | SQLite database layer. Schema (3 tables), CRUD operations, stats queries. |
| `scoring.py` | Scoring engine. S9a stub (backward compat), S9b exact match, S9c graduated scale, GLANCE composite, speed-accuracy and RT2 classification. |
| `semantic.py` | Embedding-based S9a scoring. `paraphrase-multilingual-mpnet-base-v2` (278M params, 768-dim). Model loading, reference caching, cosine similarity. |
| `analytics.py` | Aggregate statistics. Per-quadrant breakdown, speed-accuracy distribution, A/B delta with McNemar, S10 saillance rate. |
| `config.yaml` | All configuration: timer, flux mode, profile options, 15 domain question sets + generic fallback, scoring constants. |
| `config_loader.py` | YAML config reader with in-process caching. Exposes `get_constant(key, default)`. |
| `recommender.py` | Recommendation engine (explainability layer). Analyzes GA graphs for tension (high weight + low stability), unresolved energy, channel effectiveness (Cleveland & McGill + Stevens), and accessibility. Generates prioritized fixes with expected S9b impact. Powers the 99 EUR audit deliverable. |
| `pattern_registry.yaml` | Channel-to-diagnostic-question mapping. Used by recommender.py for channel upgrade paths and by the adaptive Q4/Q5 system. |
| `S2b_Mathematics.md` | Mathematical model. Defines all formulas, metrics, thresholds, statistical tests. 10 sections. |
| `generate_leurres.py` | Matplotlib generator for 10 distractor images (title cards, scatter plots, heatmaps, GA-style figures). |
| `static/style.css` | Dark-theme CSS. Design tokens, responsive layout, VEC perceptual principles applied. |
| `templates/base.html` | Jinja2 base template. HTML head, container div, block hooks. |
| `templates/index.html` | Landing page. Protocol explanation, links to onboard and dashboard. |
| `templates/onboard.html` | Profile form. Clinical domain, experience, data literacy, GRADE familiarity, color vision. |
| `templates/test.html` | Spotlight test arena. JS state machine (briefing/countdown/exposure/Q1/Q2/Q3/Q4/submitting). |
| `templates/test_flux.html` | Flux/stream test arena. JS auto-scroll feed, S10 thumbnail selection, Q1/Q2/Q3/Q4. |
| `templates/reveal.html` | Results page. GLANCE composite score, S9a/S9b/S9c cards, keystroke dynamics, comparison stats. |
| `templates/complete.html` | End screen. Shown when participant has seen all available images. |
| `templates/dashboard.html` | Analytics dashboard. Aggregate stats, speed-accuracy distribution, quadrant breakdown, A/B delta, S10 rate, stream vs spotlight split. |
| `ga_library/*.png` | 47 GA image files served at `/ga/`. |
| `ga_library/*.json` | 47 sidecar metadata per image: domain, version, correct_product, products, semantic_references. |
| `ga_library/REGISTRY.yaml` | Library index: paper source, type, hypotheses served per image. |
| `ga_library/generate_library.py` | Batch generator: 18 papers x 2 versions (bar chart + pie/bubble control) = 36 images + 36 JSONs. Plus 11 pre-existing images. |
| `ga_library/leurres/` | 10 distractor images for flux mode + `leurres.json` manifest. |
| `ga_library/leurres/leurres.json` | JSON manifest listing all leurre filenames. Read by `_load_leurres()` in `app.py`. |
| `data/glance.db` | SQLite database (auto-created on first run). |
| `docs/ARCHITECTURE.md` | This file. |
| `docs/PIPELINE.md` | GA ingestion pipeline documentation. |
| `docs/DEPLOYMENT.md` | Deployment and maintenance guide. |
| `docs/SEMANTIC_SCORING.md` | Semantic scoring architecture, calibration data, threshold justification. |
| `docs/METRICS.md` | Comprehensive metrics reference (all GLANCE metrics in one place). |

---

## Data Model

### stimulus_condition

The `stimulus_condition` field in the `tests` table records the exposure context. Currently only `nude` is implemented:

| Condition | Frame | Text | Image width | What it isolates |
|-----------|-------|------|-------------|------------------|
| `nude` | None | None | 550px | Pure design performance -- GA alone, no context |
| `title_only` | Minimal | Article title | 550px | Spoiler effect -- does the title carry the info? |
| `toc_sim` | MDPI grid | Title + authors | 200px | Survival at downscale (mobile-first) |
| `social_sim` | Twitter/LinkedIn card | Tweet/post | 500px | Social text anchoring bias |

Implementation priority: nude (MVP, done) -> title_only (V2) -> toc_sim (V3) -> social_sim (V4).

### Leurre Library

Stream mode requires distractor images that look like real scientific content but are not GA test targets. The leurre library lives at `ga_library/leurres/` and contains:

- 4 article title cards (oncology, neuroscience, epidemiology, cardiology)
- 3 scientific figures (scatter plot, Kaplan-Meier curve, gene expression heatmap)
- 3 GA-style images (bar comparison, infographic meta-analysis, PRISMA flowchart)

Generated by `generate_leurres.py` using matplotlib. All images are 1100x560px to match GA dimensions. The `leurres.json` manifest is read by `_load_leurres()` in `app.py`.

### S10 Saillance Metric

After the stream feed completes, the participant sees 3 thumbnails: the target GA + 2 random leurres. They select which image they remember. This measures scroll-stopping power:

- `s10_hit = 1` if the participant selected the target GA
- `s10_hit = 0` if they selected a distractor
- `s10_hit = NULL` for spotlight mode tests

Chance level = 1/3 = 0.33. Threshold for validated scroll-stopping = >0.70.

Computed in `analytics.compute_s10_rate()`. Displayed in dashboard with the chain metric `S10 x S9b`.

---

## Data Flow

### 1. Profile (onboard)

Participant fills a form with 5 covariables: `clinical_domain`, `experience_years`, `data_literacy`, `grade_familiar`, `colorblind_status`. A UUID token is generated, stored in `participants` table, and set as an HTTP-only cookie (`glance_token`, 30-day TTL).

### 2. Test (arena)

**Spotlight mode** (`test.html`): JS state machine with 8 states:

```
BRIEFING --[checkbox + click]--> COUNTDOWN (3s) --[auto]--> EXPOSURE (5000ms)
     --[auto]--> Q1 (free recall) --[click]--> Q2 (product choice)
     --[click]--> Q3 (actionability) --[click]--> Q4 (optional comment)
     --[click/skip]--> SUBMITTING --[form POST]--> server
```

**Flux mode** (`test_flux.html`): JS state machine with 7 states:

```
BRIEFING --[click]--> FEED (6 items, 4s each, auto-scroll)
     --[auto]--> SELECTION (3 thumbnails, S10) --[click]--> Q1 (free recall)
     --[click]--> Q2 (product choice) --[click]--> Q3 (actionability)
     --[click]--> Q4 (optional comment) --[click/skip]--> SUBMITTING --[form POST]--> server
```

During EXPOSURE/FEED, the browser listens for `visibilitychange` events (tab switches). During Q1, `keydown` events capture first/last keystroke timestamps.

All timing is measured via `performance.now()`. The hidden form collects 17 fields (spotlight) or 18 fields (flux, adds stream metadata) and POSTs to `/submit`.

### 3. Scoring

`score_test()` in `scoring.py` orchestrates:

1. **S9a (subject identification):** delegates to `semantic.score_s9a_semantic()`. Embeds user text, computes cosine similarity against cached reference embeddings, takes max. Returns `(float_score, bool_pass)` with threshold at 0.40.
2. **S9b (hierarchy perception):** exact string match of `q2_choice` against `correct_product`. Binary pass/fail.
3. **S9c (actionability):** graduated scale `{0.0, 0.5, 1.0}` mapping the three-option response (no/need_more/yes).
4. **GLANCE composite:** `0.2*S9a + 0.5*S9b + 0.3*S9c`. See `S2b_Mathematics.md` section 7.
5. **Speed-accuracy:** classifies into `{fast_right, slow_right, fast_wrong, slow_wrong}` using `RT2_FAST_SLOW_MS` (default 3000ms).

Additionally, `submit_test()` in `app.py` computes `s10_hit` for stream-mode tests by comparing `stream_selected_id` against `target_filename`.

### 3b. Score & Recommend (GA Audit)

For GA audit clients (99 EUR tier), the recommendation engine (`recommender.py`) analyzes the GA's information graph and generates actionable design fixes:

```
GA graph YAML (19 nodes, 38 links)
    |
    v
analyze_ga()
    |  scan each node for tension signals:
    |    - weight > 0.7 AND stability < 0.5 → CRITICAL (unvalidated claim)
    |    - energy > 0.6 → HIGH (unresolved design element)
    |    - weight > 0.6 AND stability > 0.8 → strength (established)
    |
    v
channel upgrade paths (UPGRADE_PATHS)
    |  area → length: +20-30% S9b (Stevens β 0.7 → 1.0)
    |  volume → length: +30-40% S9b
    |  color_saturation → luminance: +15-25% uncertainty perception
    |  color_hue → length + hue: +10-20% S9b (add redundant magnitude channel)
    |  no_channel → length: 0% → 60-80% perception
    |
    v
accessibility checks (3 checks)
    |  color_pair_close: 8% male colorblindness
    |  text_density: 30-word budget (V3)
    |  small_details: 50% readability (V7)
    |
    v
generate_report() → exports/ga_analysis_report.md
```

The output is a prioritized markdown report: CRITICAL fixes first, then HIGH, then channel upgrade table, then accessibility warnings. This report is the core deliverable of the 99 EUR GA audit product.

### 4. Reveal

After scoring, the participant sees their results: GLANCE composite as a percentage with pass/fail label (threshold 0.70), individual S9a/S9b/S9c pass/fail cards, S9a semantic similarity score, keystroke dynamics for Q1 (latency classification: <1500ms immediate, 1500-4000ms standard, >4000ms reconstruction), speed-accuracy quadrant, and the original image.

If there are other tests for the same image, comparison stats (pass rates, average Q2 time) are shown.

### 5. Dashboard

Aggregates all tests into:

- Global pass rates (S9a, S9b, S9c) and mean GLANCE composite
- Median RT2 with fluency classification (fluent/hesitant/lost)
- Speed-accuracy 4-quadrant distribution
- Per-profile-quadrant breakdown (Q1 public, Q2 tech, Q3 clinician, Q4 clinician-researcher)
- A/B delta (VEC vs control) with McNemar chi-squared if sufficient paired data
- Invalidation rate (tab-switch percentage)
- Stream vs Spotlight split: separate aggregate stats for each exposure mode
- S10 saillance rate (stream mode only) with chain metric S10 x S9b

---

## Scoring Pipeline

### Evolution: keyword -> semantic

The original S9a implementation used substring matching against a keyword list defined in `config.yaml`. This failed on paraphrases ("un truc d'immunologie" did not match "immunomodulat").

The current implementation uses `paraphrase-multilingual-mpnet-base-v2` (278M params, 768-dim embeddings, 50+ languages). User text is embedded and compared via cosine similarity against multi-level reference texts (L1 broad, L2 specific, L3 detailed). Maximum similarity across all references determines the score.

The keyword stub (`score_s9a()` in `scoring.py`) remains for backward compatibility but always returns False. All actual S9a scoring flows through `semantic.score_s9a_semantic()`.

See `docs/SEMANTIC_SCORING.md` for model selection rationale, calibration data, and threshold justification.

### Scoring path per test

```
user answer (q1_text)
    |
    v
semantic.embed(q1_text)        -- ~80ms, CPU (mpnet-base-v2)
    |
    v                           reference embeddings
cosine similarity               (cached in-memory per GA version)
    |                               |
    v                               v
max(similarities) -----> s9a_score (float)
    |
    v
s9a_score >= 0.40 ? -----> s9a_pass (bool)

q2_choice == correct_product ? -----> s9b_pass (bool)

q3_choice mapping {oui:1.0, besoin:0.5, non:0.0} -----> s9c_score (float)

0.2*s9a + 0.5*s9b + 0.3*s9c -----> glance_score (float)

s9b_pass x q2_time <> 3000ms -----> speed_accuracy (str)

stream_selected_id == target_filename ? -----> s10_hit (int, stream only)
```

---

## Key Design Decisions

### Why FastAPI + SQLite (not Django, not Postgres)

**FastAPI** because the server is a thin layer between browser forms and SQLite queries. No ORM needed. No admin panel needed. No middleware stack needed. FastAPI gives us type-checked routes, auto-docs at `/docs`, and async capability for zero cost. The entire server is ~385 lines.

**SQLite** because the expected data volume is small (hundreds to low thousands of tests). WAL mode provides concurrent read access. The database is a single file (`data/glance.db`) that can be copied, backed up, or deleted trivially. No service to manage. No connection pooling. Foreign keys enforced via `PRAGMA foreign_keys=ON`.

### Why vanilla JS (not React)

The test arena is a state machine with 7-8 states. The total JS is ~160-200 lines per template. React would add 200KB+ of runtime, a build step, and a toolchain for zero benefit. The state transitions are explicit (`showPanel(name)`), the form submission is a standard POST, and the timing instrumentation is ~10 lines of `performance.now()`.

### Why semantic scoring (not keyword matching)

Keyword matching is brittle across languages, paraphrases, and levels of specificity. Calibration showed a clean separation: off-topic answers score <0.37, correct-domain answers score >0.52. The embedding model runs locally (~80ms/call on CPU), requires no API key, and handles French/English/mixed-language input natively. See `docs/SEMANTIC_SCORING.md` for full calibration data.

### Why 5000ms exposure / 4000ms per stream item

The 5-second exposure window (spotlight) and 4-second per-item duration (stream) are grounded in cognitive science:

- **Pre-attentive processing** completes in <250ms (Treisman, 1985). This is the channel that bar length (P32) exploits.
- **Full perceptual decision** takes 1-3s for simple visual hierarchy judgments.
- **5s** is long enough for full processing but short enough to prevent strategic reading.
- **4s per stream item** matches eye-tracking data for mobile scroll (Liu et al., 2020): 2-5s mean fixation time.
- **Reference benchmark:** Akl et al. (2007) showed GRADE symbols achieve 74% comprehension. The VEC targets >=80% at 5s exposure.

### Why max-over-references (not average)

A participant may describe the GA at any level of detail. "Immunologie" (L1) and "OM-85 est le mieux documente" (L3) are both correct identifications. Taking the max cosine similarity across all reference levels ensures correct answers at any granularity pass. An average would penalize participants who happened to match one level well but not others.

---

## Database Schema

3 tables in `data/glance.db`:

**`participants`** -- one row per test-taker, identified by token cookie.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `created_at` | TEXT | `datetime('now')` |
| `token` | TEXT UNIQUE | UUID, stored in cookie |
| `clinical_domain` | TEXT | Profile covariable |
| `experience_years` | TEXT | Profile covariable |
| `data_literacy` | TEXT | Profile covariable |
| `grade_familiar` | INTEGER | 0 or 1 |
| `colorblind_status` | TEXT | Vision status |

**`ga_images`** -- one row per GA image in the library.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `filename` | TEXT | PNG filename in `ga_library/` |
| `domain` | TEXT | One of 15 domains + `generic` (see config.yaml) |
| `version` | TEXT | GA version identifier (cache key for embeddings) |
| `is_control` | INTEGER | 0 or 1 (A/B testing) |
| `correct_product` | TEXT | Expected Q2 answer |
| `products` | TEXT | JSON array of Q2 options |
| `title` | TEXT | Display title |
| `description` | TEXT | GA description |

**`tests`** -- one row per test submission. Unique on `(participant_id, ga_image_id)`.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `participant_id` | INTEGER FK | -> `participants.id` |
| `ga_image_id` | INTEGER FK | -> `ga_images.id` |
| `created_at` | TEXT | `datetime('now')` |
| `exposure_ms` | INTEGER | Default 5000 |
| `q1_text` | TEXT | Free-recall answer |
| `q1_time_ms` | INTEGER | Q1 response time |
| `q2_choice` | TEXT | Product selection |
| `q2_time_ms` | INTEGER | Q2 response time (RT2) |
| `q3_choice` | TEXT | Actionability answer |
| `q3_time_ms` | INTEGER | Q3 response time |
| `s9a_pass` | INTEGER | 0 or 1 |
| `s9a_score` | REAL | Cosine similarity float (0.0-1.0) |
| `s9b_pass` | INTEGER | 0 or 1 |
| `s9c_pass` | INTEGER | 0 or 1 (backward compat) |
| `s9c_score` | REAL | Graduated: 0.0, 0.5, 1.0 |
| `glance_score` | REAL | Composite: 0.2*S9a + 0.5*S9b + 0.3*S9c |
| `speed_accuracy` | TEXT | fast_right/slow_right/fast_wrong/slow_wrong |
| `q4_text` | TEXT | Optional free comment |
| `ab_group` | TEXT | A/B group assignment |
| `tab_switched` | INTEGER | 0 or 1 (integrity flag) |
| `exposure_actual_ms` | INTEGER | Actual exposure duration |
| `q1_first_keystroke_ms` | INTEGER | Latency to first keystroke in Q1 |
| `q1_last_keystroke_ms` | INTEGER | Timestamp of last keystroke in Q1 |
| `exposure_mode` | TEXT | `spotlight` or `stream` |
| `stream_position` | INTEGER | 1-indexed target position in feed |
| `stream_length` | INTEGER | Total items in feed |
| `stream_selected_id` | TEXT | Filename participant selected in S10 step |
| `s10_hit` | INTEGER | 1=correct selection, 0=wrong, NULL=spotlight |
| `stimulus_condition` | TEXT | Default `nude`. Future: `title_only`, `toc_sim`, `social_sim` |
| `stimulus_text` | TEXT | Accompanying text (NULL for nude condition) |

---

## Integration Points

GLANCE connects to the VEC pipeline at these interfaces:

| Interface | Direction | Mechanism |
|-----------|-----------|-----------|
| GA images | VEC -> GLANCE | PNG files in `ga_library/` with sidecar JSON |
| Leurre images | Generator -> GLANCE | `generate_leurres.py` outputs to `ga_library/leurres/` |
| Batch generation | Generator -> GLANCE | `ga_library/generate_library.py` outputs PNG + JSON pairs |
| Test results | GLANCE -> VEC | Query SQLite `tests` table for S9b pass rates per GA version |
| A/B validation | GLANCE -> VEC | `compute_ab_delta()` compares control (area-encoded) vs VEC (length-encoded) |
| S10 validation | GLANCE -> VEC | `compute_s10_rate()` measures scroll-stopping in stream mode |
| Design iteration | GLANCE -> VEC | If `Taux_S9b < 0.80` for a GA version, the VEC parameters need adjustment |
| Semantic references | VEC -> GLANCE | GA authors write L1/L2/L3 reference texts in sidecar JSON |

GLANCE has no runtime dependency on VEC code. The interface is pure file-based: images and JSON in `ga_library/`.

---

## Guarantee Loop

```
RESULT --> SENSE --> HEALTH --> CARRIER
```

| RESULT | SENSE | HEALTH | CARRIER |
|--------|-------|--------|---------|
| GA hierarchy is perceived correctly at 5s exposure | `Taux_S9b(GA)` -- proportion of participants who identify the correct hierarchy element | `Taux_S9b >= 0.80` (PASS), `0.60-0.80` (WARN), `<0.60` (FAIL) per `S2b_Mathematics.md` section 2 | Dashboard at `/dashboard` -- visible to any operator |
| VEC outperforms industry-standard area encoding | `Delta_S9b = Taux_S9b(VEC) - Taux_S9b(control)` via `compute_ab_delta()` | `Delta_S9b > +0.30` (publishable), `+0.10 to +0.30` (moderate), `<+0.10` (no difference). McNemar chi2 > 3.84 for p<0.05 significance | Dashboard A/B delta section + `mcnemar_significant` flag |
| GA captures attention in ambient scroll | `S10 rate` via `compute_s10_rate()` (stream mode only) | `S10 > 0.70` (scroll-stopping validated), `0.33-0.70` (not more memorable than distractors), `<0.33` (actively ignored) | Dashboard S10 section |
| Full chain holds: attention -> comprehension | `S10 x S9b` product (chain metric) | `> 0.56` threshold | Dashboard S10 section |
| Test integrity is maintained | `Taux_invalidation` -- proportion of tests where participant switched tabs during exposure | `<20%` normal, `>20%` signals UX or engagement problem | Dashboard invalidation rate stat |
| S9a scoring correctly separates correct from incorrect identification | `s9a_score` distribution -- cosine similarity float stored per test | Gap between off-topic (<0.37) and correct (>0.52) with threshold at 0.40 | Dashboard S9a pass rate + per-test `s9a_score` in reveal page |

---

## Constants Reference

All configurable constants live in `config.yaml` under the `constants:` key and are read via `config_loader.get_constant(key, default)`. Hardcoded phenomenon constants stay in code with `# Phenomenon:` comments. See `docs/SEMANTIC_SCORING.md` section 5 for the full constant audit.
