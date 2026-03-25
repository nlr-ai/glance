# GLANCE -- Feature Overview

GLANCE (Graphical Literacy Assessment for Naive Comprehension Evaluation) is the first standardized benchmark for measuring whether scientific Graphical Abstracts communicate their message under real-world conditions.

---

## Core Test

### Two Viewing Modes

- **Stream Mode** -- GA embedded in a simulated LinkedIn feed with inertial scroll physics (iPhone 14 frame emulation). The participant doesn't know which element will be tested. Measures comprehension under ambient attention (ecological validity).
- **Spotlight Mode** -- GA shown in isolation for 5 seconds. Measures ceiling comprehension under focused attention.

### Three Comprehension Questions

| Question | Metric | Method |
|----------|--------|--------|
| "What did you just see?" (free recall) | **S9a** | Semantic embedding cosine similarity (384d multilingual MiniLM) |
| "Which element is best documented?" (4AFC) | **S9b** | Forced choice, chance = 25% |
| "Would this change your practice?" | **S9c** | Graduated scale {0, 0.5, 1.0} |

### Voice Input

Participants can respond by voice (Web Speech API). A semantic filter automatically removes meta-talk ("um", "I don't know", "how to say") to retain only informational content. Solves the verbal production bottleneck (Levelt 1989): the participant thinks aloud, the system extracts the signal.

### System 2 Deep Analysis

After the 5-second exposure and 3 questions, participants describe everything they understand from the GA with an open microphone (90 seconds). Verbal chunks are mapped to the GA's information graph, revealing exactly **which information survives the scroll and which is lost**.

- Chunk-to-node mapping against the L3 graph
- Filter ratio (meta-talk vs. content) as cognitive effort measure
- First-utterance latency as memory trace accessibility indicator

---

## Scoring

### Individual Metrics

| Score | What it measures | How |
|-------|-----------------|-----|
| **S9a** | Subject identification | Embedding cosine similarity >= 0.40 against multi-level reference texts |
| **S9b** | Evidence hierarchy perception | 4AFC, correct = the best-documented element |
| **S9c** | Actionability | Graduated {0, 0.5, 1.0} |
| **GLANCE composite** | Weighted overall score | 0.2 * S9a + 0.5 * S9b + 0.3 * S9c |
| **Fluency** | Speed x Accuracy | S9b / log(RT2) -- fast correct > slow correct > wrong |
| **Cognitive Effort Index** | Processing difficulty | Combines filter_ratio + first-utterance latency |
| **S2 Coverage** | Information survival (System 2) | Chunks mapped / total graph nodes |

### Descriptive Verdicts

| Score | Verdict |
|-------|---------|
| >= 90% | LIMPIDE |
| >= 80% | FLUIDE |
| >= 70% | ACCESSIBLE |
| >= 60% | BRUMEUX |
| >= 40% | OPAQUE |
| < 40% | ILLISIBLE |

### Speed-Accuracy Classification

Participants are classified into quadrants based on reaction time and accuracy: Fast & Right, Fast & Wrong, Slow & Right, Slow & Wrong.

---

## Distortion Taxonomy: Spin / Drift / Warp

Three proprietary dimensions for diagnosing why a GA fails to communicate:

| Distortion | Definition | What it detects |
|-----------|-----------|----------------|
| **Spin** | Biased emphasis -- visual hierarchy doesn't match evidence hierarchy | Truncated axes, disproportionate areas, manipulative color |
| **Drift** | Encoding-induced loss -- information is present but the visual channel doesn't transmit it | Use of weak channels (area beta=0.7, saturation) instead of strong ones (length beta=1.0, position) |
| **Warp** | Selective prominence -- one element dominates at the expense of others | High sigma/mu of node coverage in the L3 graph |

The `/spin` page offers a zero-friction demonstration: a control GA (area/pie encoding) is shown for 5 seconds, the participant answers Q2, then sees a side-by-side reveal with the VEC bar chart version and the Stevens beta explanation.

---

## 7 GA Archetypes

Each tested GA receives a diagnostic archetype based on its score profile and distortion signatures:

| Archetype | Icon | Signature | Recommendation |
|-----------|------|-----------|---------------|
| **Cristallin** | Crystal | High saliency, high S9b, low distortion | Maintain this quality level -- reference for the domain |
| **Spectacle** | Circus tent | Eye-catching but no message transfer | Reduce decorative elements, strengthen data encoding |
| **Tresor Enfoui** | Gem + rock | Rich content, invisible at scroll speed | Increase visual saliency: brighter colors, larger key elements |
| **Encyclopedie** | Books | Text overload (>50 words), low S9b | Reduce to 30 words max, replace text with visual encodings |
| **Desequilibre** | Balance | Extreme warp -- one element dominates | Rebalance visual hierarchy, give space to under-represented data |
| **Embelli** | Sparkles | Effective communication but biased message | Verify visual encoding is proportional to actual effect sizes |
| **Fantome** | Ghost | Visually non-existent -- complete scroll-through | Complete redesign needed |

Classification: rule-based (not ML) with Euclidean distance fallback to ideal archetype profiles. Transparent, explainable, reproducible.

---

## AI-Powered GA Analysis

Upload any GA image (PNG, JPG, WebP, or PDF) to `/analyze` for instant AI analysis:

1. **Gemini Pro Vision** decomposes the GA into a structured L3 graph (5-15 nodes with weight, stability, energy)
2. **OCR text extraction** from the image
3. **Metadata extraction**: chart type, word count, visual channels used, hierarchy clarity, accessibility issues, color count, legend presence, figure-text ratio
4. **Auto-generated executive summary** (French)
5. **Archetype prediction** from visual metadata (vision approximation method)
6. **Prioritized recommendations** with expected delta-S9b per fix

The analysis pipeline also supports PDF upload with automatic largest-image extraction (PyMuPDF).

---

## Recommendation Engine

The recommender maps each GA's design decisions to the 75-channel visual ontology and generates actionable upgrade paths:

| Current Encoding | Upgrade To | Stevens Beta Change | Expected Improvement |
|-----------------|-----------|-------------------|---------------------|
| Area (beta=0.7) | Length (beta=1.0) | +43% | +20-30% on S9b |
| Volume (beta=0.6) | Length (beta=1.0) | +67% | +30-40% on S9b |
| Color saturation | Luminance | N/A | +15-25% on uncertainty perception |
| Color hue alone | Length + hue (redundant) | N/A | +10-20% on S9b |

Each recommendation includes the psychophysics rationale (Cleveland & McGill, Stevens, MacEachren) and expected score improvement.

---

## Analytics

### Domain Leaderboards

- 15 scientific domains: medicine, cs.AI, economics, climate, education, psychology, neuroscience, nutrition, engineering, agriculture, environmental science, sociology, marine science, energy, materials science
- 47 GAs ranked by GLANCE score within each domain
- Per-domain pages at `/leaderboard/{domain}`

### GA Detail Pages

Each GA at `/ga-detail/{id}` shows:
- Score distributions (Chart.js histograms)
- S9a/S9b/S9c breakdown
- VEC vs Control A/B comparison (delta metrics)
- Fluency analysis
- L3 graph (if available)
- Recommendations
- Archetype badge

### Participant Rankings

- **Comprehension ranking**: average GLANCE score (minimum 3 tests to qualify)
- **Contribution ranking**: total tests completed
- Percentile calculations per participant

### Admin Dashboard

Password-protected `/admin` page with Chart.js visualizations:
- Tests per day, participants per day
- Score distributions (S9a, S9b, S9c)
- Average score by domain
- KPI evolution (7d, 30d, 90d trends)

---

## Sharing

### OG Card Generation

Server-side PNG rendering (PIL, 1200x630) with GLANCE dark theme:
- **Test result cards** (`/card/{test_id}.png`): GA thumbnail, scores, verdict, archetype
- **Dashboard cards** (`/card/dashboard/{participant_token}.png`): overall stats, percentile
- **GA OG cards** (`/og/ga/{ga_id}.png`): GA image with score badge overlay
- **Default card** (`/card/default.png`): landing page social preview

### Social Share Buttons

LinkedIn, Twitter/X, and WhatsApp share buttons integrated into result and GA detail pages. Archetype name and descriptive verdict appear in the share text.

---

## Evidence Chain

GLANCE validates through 6 levels of evidence, each building on the previous:

| Level | What it proves | Key metric |
|-------|---------------|------------|
| **0** | The test measures something real (not noise) | S9b inter-GA variance sigma > 0.15 |
| **1** | The test measures comprehension (not chance) | S9b(bar) > S9b(pie) for same data |
| **2** | Stream mode is ecologically valid | S10 x S9b > 0.56 |
| **3** | Scoring explains WHY a GA fails | Channel coverage correlates with S9b |
| **4** | Recommendations improve GAs | VEC(after) > Original(before) |
| **5** | The model generalizes across domains | H1 PASS cross-domain |

If a level fails, everything above it collapses.

---

## Participant Profiling

Each participant is classified on two axes:
- **Clinical Expertise**: domain experience level
- **Analytical Literacy**: comfort with data, graphs, scientific papers, GRADE system

This enables stratified analysis: "This GA is understood at 85% by specialists but only 42% by the general public."

Additional profile fields: color vision (relevant for ~8% of male participants), input mode preference (voice/text).

---

## Technical Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI + SQLite |
| **Templates** | Jinja2 + vanilla JavaScript |
| **Semantic scoring** | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2, 384d, 50+ languages) |
| **Vision AI** | Gemini Pro Vision API |
| **Charts** | Chart.js |
| **OG cards** | Pillow (PIL) server-side rendering |
| **i18n** | Config-driven FR/EN string dictionary with cookie persistence |
| **OCR** | Pipeline on all GA images (`ocr_results.json`) |
| **Deployment** | Render.com (auto-deploy from GitHub) |

### Compliance

- RGPD compliant: explicit consent at onboarding, privacy policy (`/privacy`), terms of use (`/terms`)
- No personal health data collected
- Right to erasure supported

---

## GA Library

- 47 calibrated GA images across 15 scientific domains
- Each GA has a sidecar JSON with metadata (domain, correct answer, products, OCR text, description)
- VEC (Visual Evidence Compiler) versions paired with industry control versions for A/B comparison
- Calibrated leurres (distractors) per domain for Stream mode
- Pattern registry (`pattern_registry.yaml`) with empirical scores per visual pattern

---

*GLANCE -- Making comprehension measurable.*
*SciSense SASU -- Making Science Make Sense.*
