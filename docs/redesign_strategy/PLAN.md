# Famous Paper Redesign -- Implementation Plan

## Phase 1: Setup (This Session)

### 1.1 Ingest the 9 famous papers

For each of the 8 calendar papers + 1 worst-scored specimen, create:

| Paper | Slug | Category |
|-------|------|----------|
| Semaglutide STEP 1 (Wilding et al. 2021, NEJM) | `semaglutide_step1` | A |
| Nature Cell Biology worst-scored | `ncb_worst` | B |
| BNT162b2 (Polack et al. 2020, NEJM) | `bnt162b2_pfizer` | A |
| AlphaFold (Jumper et al. 2021, Nature) | `alphafold_jumper` | A |
| Watson & Crick (1953, Nature) | `watson_crick_dna` | C |
| Lecanemab (van Dyck et al. 2023, NEJM) | `lecanemab_clarity` | A |
| Microplastics (Leslie et al. 2022, Env Int) | `microplastics_blood` | A |
| Lowry protein assay (1951, JBC) | `lowry_protein` | C |

Per paper:

1. **Locate the original GA** (or confirm absence for Category C)
2. **Save image** to `ga_library/redesigns/{slug}_before.png`
3. **Write sidecar JSON** to `ga_library/redesigns/{slug}_before.json` with:
   - `domain`, `version`, `correct_product`, `products`, `title`, `description`
   - `semantic_references` (L1/L2/L3)
   - `category`: `"A"` / `"B"` / `"C"`
   - `citation`: full reference string
4. **For Category C papers**: create a "no GA" placeholder image (grey card with paper title + "No Graphical Abstract" + year)

### 1.2 Score each original with GLANCE pipeline

For each `{slug}_before.png`:

```bash
cd C:\Users\reyno\scisense\glance
python channel_analyzer.py ga_library/redesigns/{slug}_before.png ga_library/redesigns/{slug}_before_graph.yaml
python recommender.py ga_library/redesigns/{slug}_before_graph.yaml
```

Record the scores:
- GLANCE composite
- Channel analysis (which channels are used, effectiveness)
- Recommendation report (CRITICAL/HIGH issues, channel upgrade paths)

For Category C papers (no GA): assign score 0% with archetype "Absent" and note "No Graphical Abstract exists for this paper."

### 1.3 Build the scoring registry

Create `ga_library/redesigns/REGISTRY.yaml`:

```yaml
redesigns:
  semaglutide_step1:
    paper: "Wilding et al. (2021) NEJM 384:989-1002"
    category: A
    before_score: null  # filled after scoring
    after_score: null    # filled after redesign
    delta: null
    week: 1
    voice: aurore
    status: ingested
```

---

## Phase 2: First Redesign -- Ozempic (Week 1)

### 2.1 Define the redesign intent

Run `ga_advisor.py` with a precise intent:

```bash
python ga_advisor.py \
  ga_library/redesigns/semaglutide_step1_before.png \
  ga_library/redesigns/semaglutide_step1_before_graph.yaml \
  "Create a GA that communicates: 95% efficacy endpoint met, N=1961, weight loss 14.9% vs 2.4% placebo, in 5 seconds. Use length encoding for the primary comparison."
```

This produces a modified graph YAML with specific node/link changes.

### 2.2 Generate the redesign parametrically

Use the `compose_paper_ga.py` architecture (adapted for the redesign data):

1. Create a layout config at `ga_library/redesigns/semaglutide_step1_layout.yaml`:
   - Left zone: key finding statement
   - Right zone: horizontal bars (semaglutide vs placebo weight loss)
   - Bottom: citation + GLANCE score badge

2. Create a palette config at `ga_library/redesigns/semaglutide_step1_palette.yaml`:
   - Dark background (`#0f172a`)
   - Accent colors for semaglutide (blue) vs placebo (neutral grey)

3. Render:
   ```bash
   cd C:\Users\reyno\scisense\glance\ga_paper
   python compose_paper_ga.py --config ../ga_library/redesigns/semaglutide_step1_layout.yaml
   ```

Output: `ga_library/redesigns/semaglutide_step1_after.png`

### 2.3 Score the redesign

```bash
python channel_analyzer.py ga_library/redesigns/semaglutide_step1_after.png ga_library/redesigns/semaglutide_step1_after_graph.yaml
python recommender.py ga_library/redesigns/semaglutide_step1_after_graph.yaml
```

Record: GLANCE composite, archetype, channel analysis.

### 2.4 Generate the side-by-side image

Create a 1200x628 composite:

```
+--- 600px ---+--- 600px ---+
|   BEFORE    |    AFTER    |
|             |             |
|  original   |  redesign   |
|   GA        |   GA        |
|             |             |
| Score: X%   | Score: Y%   |
+-------------+-------------+
|       Delta: +Z%          |
+---------------------------+
```

Script: `ga_library/redesigns/generate_sidebyside.py` (matplotlib or Pillow composite).

### 2.5 Write the 200-word diagnosis

Template:

> **Semaglutide (Ozempic) -- STEP 1 Trial**
>
> The paper that launched a $50B drug. The GA that nobody remembers.
>
> GLANCE scored the original at X%. [Channel analyzer] found [specific issues: area encoding compressing the weight loss delta, no clear hierarchy between semaglutide and placebo, etc.].
>
> The redesign uses length encoding for the primary comparison (14.9% vs 2.4% weight loss). Stevens' power law predicts a [+Y%] improvement in perceived magnitude accuracy -- and GLANCE confirms: the redesign scores Z%.
>
> [One specific insight about what the VEC changed and why it works perceptually.]
>
> Score yours. Template: glance.scisense.fr/template

---

## Phase 3: Content Production (Weeks 2-8)

### Weekly workflow

Each week, one paper goes through the full pipeline:

| Step | Time | Who |
|------|------|-----|
| 1. Score the original | 30 min | Automated (pipeline scripts) |
| 2. Run ga_advisor with intent | 15 min | Author of the week |
| 3. Generate redesign parametrically | 30 min | Automated (compose_paper_ga) |
| 4. Score the redesign | 15 min | Automated |
| 5. Generate side-by-side image | 10 min | Script |
| 6. Write 200-word diagnosis | 30 min | Author of the week |
| 7. Format for each platform | 20 min | Author of the week |

Total per redesign: ~2.5 hours.

### Voice alternation

| Week | Paper | Author | Angle |
|------|-------|--------|-------|
| 1 | Semaglutide | Aurore | Clinical: "The drug everyone talks about. The GA nobody looked at." |
| 2 | NCB worst-scored | Nicolas | Data: "Our pipeline found this. Here's what 12% looks like." |
| 3 | BNT162b2 | Aurore | Clinical: "The vaccine paper. 95% efficacy. 23% comprehension." |
| 4 | AlphaFold | Nicolas | Tech: "AI solved protein folding. The GA didn't fold well either." |
| 5 | Watson & Crick | Aurore | Storytelling: "What if the double helix had a Graphical Abstract?" |
| 6 | Lecanemab | Aurore | Clinical: "The Alzheimer's drug. The GA that needed treatment." |
| 7 | Microplastics | Nicolas | Data: "Microplastics in your blood. Macro-problems in this chart." |
| 8 | Lowry | Nicolas | Data: "The most cited paper ever. Zero visual communication." |

### Deliverables per redesign

1. **Side-by-side image** (1200x628 PNG) -- the hero content
2. **Diagnosis text** (200 words max) -- the post body
3. **Redesign GA** (standalone PNG) -- downloadable
4. **Template download CTA** -- link to 29 EUR Stripe checkout
5. **Redesign document** (REDESIGN_TEMPLATE.md format) -- internal record

---

## Phase 4: Distribution

### LinkedIn

- **Aurore's profile** for clinical papers (Weeks 1, 3, 5, 6): immunology, pharmacology, clinical trials
- **Nicolas's profile** for data/tech papers (Weeks 2, 4, 7, 8): perception, AI, data visualization
- Post format: side-by-side image + diagnosis text + template CTA
- Hashtags: #GraphicalAbstract #SciComm #DataVisualization #GLANCE
- Tag relevant accounts: journal accounts, original authors (respectfully), science communication accounts
- Publication time: Tuesday 8:00-9:00 CET

### Reddit

| Subreddit | Which papers | Angle |
|-----------|-------------|-------|
| r/dataisugly | Category B (worst scored) | "GLANCE scored this published GA at 12%. Here's the redesign." |
| r/dataisbeautiful | Category A redesigns with large delta | "Before/after of the Ozempic trial GA. +47% comprehension." |
| r/MedicalWriters | Clinical papers (semaglutide, BNT162b2, lecanemab) | Professional angle, template CTA |
| r/labrats | All | "Your PI's GA scored 23%. Here's how to fix it." |
| r/AcademicPapers | Category C (Watson & Crick, Lowry) | Historical angle, "What if..." |

### Twitter/X

- Thread format: image tweet + 3-4 reply tweets with diagnosis
- Tweet 1: side-by-side image + one-line hook
- Tweet 2: what GLANCE detected (2-3 specific issues)
- Tweet 3: what the VEC changed (2-3 specific fixes)
- Tweet 4: template CTA + link

### Blog (glance.scisense.fr/blog)

- Each redesign gets a permanent page at `/blog/redesign-{N}-{slug}`
- Full diagnosis text + side-by-side image + downloadable redesign + template CTA
- SEO: target "[paper name] graphical abstract" long-tail keywords
- Internal links to `/` (GLANCE platform) and `/template` (29 EUR checkout)

---

## File Structure

```
ga_library/
  redesigns/
    REGISTRY.yaml
    generate_sidebyside.py
    semaglutide_step1_before.png
    semaglutide_step1_before.json
    semaglutide_step1_before_graph.yaml
    semaglutide_step1_after.png
    semaglutide_step1_after.json
    semaglutide_step1_after_graph.yaml
    semaglutide_step1_layout.yaml
    semaglutide_step1_palette.yaml
    semaglutide_step1_sidebyside.png
    semaglutide_step1_diagnosis.md
    ...
    (repeat for each paper)

docs/
  redesign_strategy/
    STRATEGY.md          # Content strategy (this companion doc)
    PLAN.md              # This file
    REDESIGN_TEMPLATE.md # Template for each redesign document
```
