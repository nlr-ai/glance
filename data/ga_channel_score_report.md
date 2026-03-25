# GLANCE GA — Visual Channel Score Report

**Date:** 2026-03-25
**Scorer:** Silas (visual channel catalog L3 graph v1)
**Target:** `glance_ga_graph.yaml` (13 nodes, 19 links)
**Reference:** `visual_channel_graph.yaml` (75 channels in 8 spaces)

---

## Overall Score: 0.74 / 1.00

The GLANCE GA uses its strongest encoding channels (length, position on common scale) optimally for the solution hierarchy, but under-encodes the problem space and evidence citations. The right half of the GA is well-engineered; the left half and supporting evidence rely too heavily on text and numbers without pre-attentive visual reinforcement.

---

## Per-Node Breakdown

| GA Node | Score | Category | Primary Channels Used |
|---------|-------|----------|----------------------|
| GRADE (74%) | **0.88** | Solution | Length + Position (both beta ~1.0) + Number + Luminance |
| GLANCE (>=80%) | 0.84 | Solution | Length + Position + Number + Luminance + Bold |
| Zone Solution | 0.81 | Structure | Position + Reading direction + Common region + Hierarchy levels |
| Zone Probleme | 0.80 | Structure | Position + Reading direction + Palette temperature + Common region |
| Vanity (~0%) | 0.80 | Solution | Length (near-zero) + Position + Luminance + Hue |
| Le Gap | 0.74 | Problem | Position + Orientation + Negative space + Hue |
| Engagement (x7) | 0.73 | Problem | Numbers + Hue + Bold |
| Comprehension (0) | 0.72 | Problem | Numbers + Luminance + Proximity |
| GA Thumbnail | 0.66 | Problem | Image category + Border + Professional markers |
| SciSense | 0.65 | Actor | Branding + Contrast + Position |
| Visual Spin | **0.63** | Problem | Area + Saturation + Edge sharpness |
| 6 RCTs | 0.63 | Evidence | Numbers + Font size + Proximity |
| Akl 2007 | **0.60** | Evidence | Numbers + Font size + Connectedness |

### Category Averages

| Category | Avg Score | Assessment |
|----------|-----------|------------|
| Solution nodes | 0.84 | Strong. Optimal channel use. |
| Zone spaces | 0.81 | Good. Structural encoding works. |
| Problem nodes | 0.70 | Below target. Relies on text/numbers, lacks pre-attentive encoding. |
| Actor | 0.65 | Acceptable for intentionally discreet attribution. |
| Evidence nodes | 0.62 | Weak. Expert-only notation. Citations will not be processed in 5 seconds. |

---

## Top 5 Strengths

### 1. Length + Position dual encoding for the hierarchy (effectiveness: 0.95)
The GLANCE > GRADE > Vanity hierarchy uses the two highest-accuracy perceptual channels simultaneously. Both have Stevens beta ~1.0. This is textbook-optimal per Cleveland & McGill. The viewer perceives the hierarchy magnitude with near-zero distortion.

### 2. Common baseline alignment (effectiveness: 0.95)
All three hierarchy bars share a single baseline, enabling the fastest and most accurate magnitude comparison. This avoids the 10-20% accuracy penalty of non-aligned scales.

### 3. Ordinal luminance encoding (supplementary channel)
Dark-to-light mapping across GLANCE (darkest) > GRADE > Vanity (lightest) provides a redundant encoding that reinforces the length hierarchy. Luminance is the most intuitive channel for certainty/strength (MacEachren 2012).

### 4. Zone structure via common region
The two-zone design (problem left, solution right) exploits Gestalt common region grouping to create two clear perceptual units. This pre-attentively organizes the 13 nodes into two manageable clusters.

### 5. Natural frequency labeling
>=80%, 74%, ~0% are immediately comprehensible percentages. The 7.7x multiplier uses natural ratio format. These follow Garcia-Retamero & Cokely 2017 recommendations for numeracy-inclusive communication.

---

## Top 5 Gaps

### 1. Evidence citations have no pre-attentive encoding (Akl 2007: 0.60)
**The problem:** Akl 2007 and the 6 RCTs corpus rely entirely on text-heavy encoding (numbers, font size, statistical notation). No bars, no icons, no positional anchoring. Within 5 seconds, most viewers will not reach or process these nodes.

**What to do:** Add mini data-viz elements. A small bar chart (74% vs 14%) next to the Akl citation. A row of 6 small study icons for the RCT corpus. These pre-attentive signals communicate evidence quality without requiring reading.

### 2. The Gap magnitude is not encoded with length/area (Gap: 0.74)
**The problem:** The engagement-comprehension gap is the thesis of the paper, but its magnitude (x7 engagement vs 0 comprehension) is not encoded using the highest-accuracy channels. The scissors chart uses orientation and negative space, which are less precise.

**What to do:** Add a length-based gap indicator. A single bar showing the gap magnitude (e.g., filled bar = engagement, empty bar = comprehension, on the same common scale) would make the x7 vs 0 contrast instantly scannable.

### 3. Visual Spin lacks a self-demonstrating visualization (Spin: 0.63)
**The problem:** The spin concept (Stevens beta ~0.7 compresses area) is encoded using the very channels it warns about (area, saturation). The node explains spin but does not demonstrate it visually. This is the hardest concept in the GA and has the weakest channel assignment.

**What to do:** Create a split-view: show a bubble at physical size alongside its perceived size (at 0.7x compression). Two bars side by side — "actual" vs "perceived" — would use the optimal length channel to demonstrate the distortion the viewer cannot see.

### 4. No compound cognitive load management
**The problem:** With 13 nodes across 2 zones, multiple text labels, numerical annotations, and a scissors chart, the GA's total cognitive load is unquantified. No compound metric exists to verify the GA stays within the 5-second scan budget.

**What to do:** Count visual elements: aim for 15-20 max. Count distinct colors: aim for 4 max. Count text words: aim for 30 max (V3). Count hierarchy levels: aim for 3 max. If any exceeds threshold, simplify.

### 5. Figure-ground contrast not specified
**The problem:** The evidence hierarchy bars are assumed to be "figure" against "ground," but no minimum contrast ratio is specified. At mobile scale (V7), insufficient contrast makes the hierarchy invisible.

**What to do:** Specify WCAG 4.5:1 minimum contrast ratio for all evidence-encoding elements. Test at mobile scale (200px width TOC thumbnail) to verify bars and labels remain distinguishable.

---

## Recommendations for Marco

### Priority 1: Encode the gap with length, not just orientation
The scissors chart is conceptually elegant but perceptually imprecise. Add a complementary length-based element: two bars (engagement vs comprehension) on a shared scale next to or above the scissors chart. This makes the x7 vs 0 contrast pre-attentively scannable.

### Priority 2: Give evidence citations visual anchoring
Move Akl 2007 and 6 RCTs from pure text to mini data visualizations. A tiny forest plot, a row of study icons, or a small bar chart. These need to communicate evidence quality in <1 second, not require reading statistical notation.

### Priority 3: Demonstrate spin, do not just describe it
The spin node should contain a visual that demonstrates Stevens beta compression. Show "actual effect size" (tall bar) next to "perceived via area encoding" (compressed bar at 0.7x). The GA should be its own evidence for the perceptual distortion it documents.

### Priority 4: Specify a visual identity system
Define: font pair, 4-color palette, grid system, contrast minimums. This builds credibility gestalt — the compound signal that says "this was made with scientific care." Currently, individual elements are well-designed but no unifying visual system is documented.

### Priority 5: Enforce the 3-level hierarchy cap
Zone structure (level 1), bar hierarchy (level 2), labels/citations (level 3). If the current design has more than 3 visual hierarchy levels, it will overwhelm the 5-second window. Audit and flatten.

---

## Channel Usage Summary

| Channel Category | Channels Used | Channels Available | Usage Rate |
|-----------------|---------------|-------------------|------------|
| Pre-attentive | 12 / 19 | 63% | Good — spatial position, hue, luminance, size, proximity, similarity, continuity, common region, closure, orientation, figure-ground, onset |
| Encoding (C&M) | 4 / 9 | 44% | Adequate — position, length, area, saturation. Missing: non-aligned, angle, volume (correctly), texture, hue-categories |
| Social | 3 / 9 | 33% | Low but appropriate — only branding, platform chrome, avatar relevant for this GA type |
| Typography | 3 / 8 | 38% | Low — font weight, font size, text contrast used. Missing: family, caps, color, alignment, spacing |
| Image-level | 5 / 9 | 56% | Moderate — category, density, professional markers, resolution, border used |
| Layout | 4 / 6 | 67% | Good — reading direction, common region, negative space, visual hierarchy |
| Emotional | 4 / 9 | 44% | Moderate — numbers, data viz, branding, color-emotion used |
| Compound | 0 / 5 | 0% | None. No compound metrics computed. |

**Overall channel utilization: 35 / 75 = 47%**

This is appropriate — not all channels should be used simultaneously (that would cause overload). The critical finding is that the *most effective* channels are well-utilized for the solution hierarchy, but under-utilized for the problem space and evidence layer.

---

*Report generated from visual_channel_graph.yaml (75 channels, 8 spaces) scored against glance_ga_graph.yaml (13 nodes, 19 links).*
