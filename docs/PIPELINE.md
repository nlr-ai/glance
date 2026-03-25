# GLANCE Premier Regard -- GA Ingestion Pipeline

## Overview

The GA library (`ga_library/`) is the test stimulus set. Each entry is a GA image (PNG) plus a sidecar JSON file containing metadata and semantic reference texts. Images are auto-seeded into the SQLite database on first server startup (when `ga_images` table is empty).

**Current library:** 47 images across 15 domains + generic, with A/B control variants for each paper. 10 leurre distractor images for flux mode. Target: 50+ images, expanding domain coverage.

---

## Batch Generation: generate_library.py

The primary tool for creating the library at scale is `ga_library/generate_library.py`. It encodes 18 papers as data definitions and renders two versions of each:

- **Bar chart** (VEC-style, horizontal bars, dark background, Stevens beta ~1.0)
- **Control** (pie chart or bubble chart, area-encoded, Stevens beta ~0.7)

```bash
cd C:\Users\reyno\scisense\glance\ga_library
python generate_library.py
```

This produces 36 PNG images + 36 sidecar JSON files in a single run. Each JSON includes complete `semantic_references` (L1/L2/L3) for S9a scoring.

### What the generator produces per paper

| Output | File | Purpose |
|--------|------|---------|
| VEC bar chart | `{slug}.png` | Length-encoded GA (test stimulus) |
| VEC metadata | `{slug}.json` | Domain, correct answer, products, semantic_references |
| Control chart | `{slug}_control.png` | Area-encoded control (A/B comparison) |
| Control metadata | `{slug}_control.json` | Same as VEC but `is_control: true` |

### Visual style

- Dark background (`#0f172a`), light text (`#e2e8f0`)
- 8-color palette (colorblind-friendly): blue, orange, green, pink, purple, amber, sky, rose
- Horizontal bars sorted by value (highest on top)
- Value labels on bars, source citation at bottom
- DPI: 150, dimensions: 11x5.6 inches (1650x840px output)

---

## Pipeline Steps

### SELECT -> EXTRACT -> RENDER -> CONTROL -> TAG -> DROP -> SEED -> RECOMMEND

```
1. SELECT      Choose a paper with a clear evidence hierarchy
                |
2. EXTRACT      Identify the key finding, products/methods, correct answer
                |
3. RENDER       Generate the GA image (VEC bar chart or reference)
                |
4. CONTROL      Create A/B control variant (area-encoded version of same data)
                |
5. TAG          Write sidecar JSON with metadata + semantic_references
                |
6. DROP         Place PNG + JSON in ga_library/
                |
7. SEED         Restart server (or fresh DB) to auto-seed
                |
8. RECOMMEND    Run recommender.py on the GA graph → prioritized fixes report
```

For batch generation, steps 2-6 are automated by `generate_library.py`.

---

## Step 1: SELECT -- Choose a Paper

### Selection criteria

The paper must have:

1. **A quantitative comparison** between 3-6 named products/methods/models
2. **A clear winner** -- one element has demonstrably stronger evidence than the others
3. **Publishable data** -- values from tables/figures in the paper can be legally reproduced
4. **Domain alignment** -- matches a configured domain in `config.yaml`

### Hypothesis-driven selection

Each paper should serve at least one testable hypothesis from `S2b_Mathematics.md` section 4:

| Hypothesis | What it tests | Paper requirement |
|------------|--------------|-------------------|
| **H1** | VEC is universally readable (across profiles) | Any paper with a clear hierarchy |
| **H2** | Data literacy improves decoding | Paper where bar charts are the primary encoding |
| **H3** | Clinical expertise adds a recognition channel | Medical paper where domain knowledge helps |
| **H4** | Colorblindness breaks the signal | Paper where GA relies on color differentiation |
| **A/B delta** | VEC outperforms area encoding | Paper with both VEC and control versions |

### 15 domains currently covered

| Domain key | Label | Papers | Domain key | Label | Papers |
|------------|-------|--------|------------|-------|--------|
| `med` | Medical | 3 | `neuroscience` | Neurosciences | 2 |
| `tech` | Tech / IA | 1 | `nutrition` | Nutrition / Sante publique | 2 |
| `policy` | Politique de sante publique | 1 | `energy` | Energie / Ingenierie | 2 |
| `education` | Education | 1 | `epidemiology` | Epidemiologie | 2 |
| `climate` | Climat / Environnement | 1 | `ecology` | Ecologie / Biologie | 2 |
| `psychology` | Psychologie | 3 | `transport` | Transport / Urbanisme | 1 |
| `economics` | Economie | 2 | `agriculture` | Agriculture | 1 |
| `materials` | Science des materiaux | 1 | `generic` | Generique (fallback) | -- |

Each domain has tailored Q1/Q2/Q3 questions in `config.yaml` under `domains:`.

---

## Step 2: EXTRACT -- Identify Key Data

From the paper, extract:

- **Products/methods** (3-6 named items): these become Q2 answer options
- **Correct answer**: the item with the strongest evidence/highest score
- **Quantitative values**: the numbers that the GA will encode
- **Domain**: which `config.yaml` domain this falls under (determines Q1/Q2/Q3 wording)

In `generate_library.py`, this is the `PAPERS` list: each entry has `slug`, `domain`, `version`, `title`, `description`, `source`, `labels`, `values`, `unit`, `correct`, and `semantic_references`.

---

## Step 3: RENDER -- Generate the GA Image

Produce a PNG of the Graphical Abstract. This can be:

- **VEC parametric**: generated by `generate_library.py` -- horizontal bar chart, dark background, length-encoded
- **Infographic/reference**: an AI-generated or manually created reference image for calibration
- **Existing chart**: a bar chart or figure from the paper itself

Image requirements:
- Format: PNG (also accepts JPG, JPEG, WEBP -- see `_seed_images()` in `app.py`)
- Naming: `{short_name}.png` (no spaces, lowercase with underscores)
- Size: reasonable for web display (flux feed container is max 580px wide)

---

## Step 4: CONTROL -- Create A/B Control Variant

For A/B testing, create a control version of the same data using **area encoding** (circles, pie charts, bubble charts) instead of the VEC's length encoding (bars).

The control must:
- Contain **exactly the same data** as the VEC version
- Use **area as the primary visual encoding** (Stevens power law exponent ~0.7 for area vs ~1.0 for length)
- Have the same `correct_product`
- Be marked `is_control: true` in its sidecar JSON

`generate_library.py` automatically generates pie chart controls for each bar chart. For education domain, a bubble chart control is used instead.

Naming convention: `{short_name}_control.png` or `{short_name}_pie_control.png` / `{short_name}_bubble_control.png`.

---

## Step 5: TAG -- Write Sidecar JSON

Every image needs a sidecar JSON file with the same base name: `{short_name}.json`.

### Required fields

```json
{
    "domain": "med",
    "version": "V10.4",
    "correct_product": "OM-85",
    "products": ["OM-85", "PMBL", "MV130", "CRL1505"],
    "title": "Immunomodulateurs RTIs -- VEC V10 wireframe",
    "description": "Short description of what the GA shows"
}
```

| Field | Type | Purpose |
|-------|------|---------|
| `domain` | string | Must match a key in `config.yaml` `domains:` section. Determines Q1/Q2/Q3 question wording. |
| `version` | string | Unique version identifier. Used as cache key for semantic embeddings. |
| `is_control` | bool | `true` for A/B control images. Default `false` (omit for VEC images). |
| `correct_product` | string | Expected Q2 answer. Must exactly match one entry in `products`. Case-insensitive comparison in `score_s9b()`. |
| `products` | list[string] | Q2 answer options rendered as buttons. Include 3-6 items. |
| `title` | string | Display title on reveal page and dashboard. |
| `description` | string | Short description. Used as fallback for semantic scoring if `semantic_references` is absent. |

### Semantic references (critical for S9a scoring)

```json
{
    "semantic_references": {
        "L1_broad": ["immunologie", "infections respiratoires"],
        "L2_specific": ["comparaison de traitements immunomodulateurs pour les RTIs chez les enfants"],
        "L3_detailed": ["OM-85 possede le plus haut niveau de preuve"]
    }
}
```

This field drives the entire S9a scoring pipeline via `semantic.py`. Without it, S9a falls back to title+description matching (lower quality) or the keyword stub (always returns False).

**Reference text guidelines:**
- **L1:** 2-5 short phrases. Broad domain terms. Include French and English.
- **L2:** 2-4 sentences. Describe the comparison without naming the winner.
- **L3:** 1-3 sentences. State the main finding/hierarchy explicitly.
- No accents required (model handles both).
- Avoid standalone product names in L1/L2 -- they belong in L3 context.
- Write what a correct participant would say, not the paper title.

---

## Step 6: DROP -- Place Files

Drop the PNG and JSON files into `ga_library/`:

```
ga_library/
  my_new_paper.png
  my_new_paper.json
  my_new_paper_control.png
  my_new_paper_control.json
```

The filenames must share the same base name (everything before the extension).

---

## Step 7: SEED -- Load into Database

Images are seeded into the `ga_images` table by `_seed_images()` in `app.py`. This function runs on server startup and **only seeds if the table is empty** (`get_image_count() > 0` short-circuits).

To add new images to an existing database:

- **Option A (recommended):** Delete `data/glance.db` and restart the server. All 47 images in `ga_library/` will be seeded.
- **Option B:** Keep existing data by manually inserting via SQLite.

After adding or editing semantic_references in JSON files, call `semantic.clear_cache()` or restart the server to force re-embedding.

---

## Step 8: RECOMMEND -- Generate Actionable Fixes

After the GA is tested (or before, as a design-time audit), run the recommendation engine on the GA's information graph to get prioritized, actionable design changes.

```bash
cd C:\Users\reyno\scisense\glance
python recommender.py data/glance_ga_graph.yaml
```

This produces `exports/ga_analysis_report.md` with:

1. **CRITICAL fixes** -- nodes with high weight but low stability (claims without empirical backing)
2. **HIGH fixes** -- nodes with high energy (unresolved design elements)
3. **Strengths** -- nodes that are well-established (high weight + high stability)
4. **Accessibility warnings** -- colorblindness, text density, small-detail readability
5. **Channel upgrade paths** -- specific encoding substitutions with expected S9b improvement

### How recommendations are generated

The engine scans every node in the GA graph for tension signals:

| Signal | Condition | Priority | Meaning |
|--------|-----------|----------|---------|
| Unvalidated claim | `weight > 0.7 AND stability < 0.5` | CRITICAL | The GA asserts something it hasn't proven |
| Unresolved design | `energy > 0.6` | HIGH | The visual encoding for this element is not finalized |
| Established | `weight > 0.6 AND stability > 0.8` | (strength) | Solid -- backed by data or settled design |

Channel upgrade paths are derived from Cleveland & McGill (1984) and Stevens (1957). The key substitution: **area -> length** gains +20-30% on S9b because Stevens beta goes from 0.7 to 1.0.

### Integration with the 99 EUR audit

The recommendation report is the core deliverable of the GLANCE GA Audit product. The client receives:
- The raw GLANCE test scores (S9a, S9b, S9c, composite)
- The recommendation report with exact fixes and expected impact
- Channel upgrade paths specific to their GA's encoding choices

This is what separates a score from a service.

---

## REGISTRY.yaml

The registry at `ga_library/REGISTRY.yaml` is a human-maintained index of the library. It is **not read by code** -- it exists for documentation and planning purposes.

### Format

```yaml
images:
  short_name:
    paper: "Citation"
    domain: med|tech|policy|education|climate|psychology|economics|neuroscience|nutrition|energy|epidemiology|ecology|transport|agriculture|materials|generic
    type: vec|calibration_reference|chart|control_ab
    hypotheses: [H1, H2, ...]
    correct: "Product Name"
    added: "YYYY-MM-DD"
    notes: "Optional notes"
```

### Type taxonomy

| Type | Meaning |
|------|---------|
| `vec` | Generated by the Visual Evidence Compiler (parametric, length-encoded) |
| `calibration_reference` | AI-generated or manually created reference infographic |
| `chart` | Bar chart generated by `generate_library.py` or from a paper |
| `control_ab` | Area-encoded control version for A/B testing (pie chart, bubble chart) |

### Current registry: 47 entries across 20 papers

| Domain | Papers | Chart entries | Control entries |
|--------|--------|---------------|-----------------|
| med | 2 (immunomod) | 2 (wireframe + infographic) | 1 (area control) |
| tech | 1 (Transformer) | 1 | 1 (pie control) |
| policy | 1 (Oregon Health) | 1 | 1 (pie control) |
| education | 1 (Hattie) | 1 | 1 (bubble control) |
| climate | 1 (Drawdown) | 1 | 1 (pie control) |
| psychology | 3 (Milgram, Marshmallow, CBT) | 3 | 3 (pie controls) |
| economics | 2 (Card-Krueger, Banerjee) | 2 | 2 (pie controls) |
| neuroscience | 2 (Walker, Erickson) | 2 | 2 (pie controls) |
| nutrition | 2 (PREDIMED, Sugar Tax) | 2 | 2 (pie controls) |
| energy | 2 (Battery, LCOE) | 2 | 2 (pie controls) |
| epidemiology | 2 (COVID vaccine, Handwashing) | 2 | 2 (pie controls) |
| ecology | 2 (Pollinator, Coral) | 2 | 2 (pie controls) |
| transport | 1 (ITF emissions) | 1 | 1 (pie control) |
| agriculture | 1 (Ponisio) | 1 | 1 (pie control) |
| materials | 1 (Concrete CO2) | 1 | 1 (pie control) |

---

## Growth Strategy

### Current state

47 images across 15 domains. Every paper has both a VEC bar chart and an area-encoded control. Semantic references are embedded in every sidecar JSON. The library is sufficient for:

- Per-image S9b rate analysis
- Cross-domain H1 universality testing
- A/B delta computation for every paper

### Priority order for expansion

1. **Additional papers in under-represented domains** -- transport, agriculture, materials have only 1 paper each. 2 per domain minimum for intra-domain comparison.
2. **VEC parametric images** -- the current bar charts are generated by matplotlib, not the VEC engine. Real VEC-generated images (with P32 length encoding, P34 luminance, micro-anchors) are the target stimuli.
3. **Diverse chart types** -- beyond horizontal bars. Stacked bars, grouped bars, dot plots. Each tests different perceptual channels.
4. **Color-reliant GAs** -- to test H4 (colorblindness breaks the signal).
5. **Multiple VEC versions of the same data** -- tests design iteration (did V11 improve over V10?).

### Minimum viable library for statistical tests

| Test | Requirement | Images needed |
|------|-------------|---------------|
| Per-image S9b rate | N >= 5 per image | 1 image, 5 participants |
| Chi-squared S9b x quadrant | N >= 5 per cell, 4 cells | 1 image, 20 participants |
| McNemar A/B delta | N >= 10 paired | 1 VEC + 1 control, 10 participants who see both |
| Cross-domain H1 | S9b comparable across domains | 2+ domains, 20+ per domain |
| S10 saillance | Stream mode, N >= 10 | 1 GA + leurres, 10 stream-mode participants |

### Leurre expansion

Current: 10 leurres. Flux mode uses `n_items - 1 = 5` per feed. With 10 leurres, each test draws a random sample of 5, providing moderate variety. For large-scale deployment, 20-30 leurres would ensure participants rarely see the same distractor twice.

Leurres are generated by `generate_leurres.py` and must be regenerated if new types are needed:

```bash
cd C:\Users\reyno\scisense\glance
python generate_leurres.py
```
