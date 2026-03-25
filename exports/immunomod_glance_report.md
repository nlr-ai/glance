# GLANCE Analysis Report — Immunomodulator GA

**"Bacterial-derived immunomodulators as promising preventive strategies"**

**Date:** 2026-03-25 | **Analyst:** GLANCE Recommendation Engine v1 | **Subject:** MDPI Children paper GA

---

## Section 1: GA Overview

### Description

This Graphical Abstract presents the case for bacterial-derived immunomodulators as preventive strategies against pediatric respiratory infections. The GA uses a **three-panel layout**:

- **Left panel ("Early life window"):** Pathological cascade showing inflammation, epithelial injury, airway remodeling, recurrent wheezing, and risk of asthma. Includes an illustration of a sick child.
- **Central panel (Bronchial cross-section):** Longitudinal cross-section of bronchial tissue showing 4 tissue layers (lumen, epithelium, lamina propria, smooth muscle) with explicitly labeled immune cells: Macrophage, Dendritic Cell, Neutrophil Cell, T Cell, NK Cell, B Cell producing IgA/IgG. Four immunomodulators (OM-85, PMBL, CRL1505, MV130) are positioned at their respective tissue-layer targets. Four mechanism boxes at the bottom describe: Epithelial Barrier Reinforcement, Innate Immunity Activation, Adaptive Immunity Modulation, and Inflammation Control & Gut-Lung Axis.
- **Right panel ("Clinical data"):** Bar chart encoding evidence hierarchy: OM-85 (18 RCTs), PMBL (5 RCTs), MV130 (1 RCT), CRL1505 (Preclinique).

### L3 Graph Summary

| Metric | Value |
|--------|-------|
| Total nodes | 40 |
| Total links | 60 |
| Node types | 5 spaces, 20 things, 4 narratives, 2 actors, 4 moments, 5 immune cells |
| Overall score (w*s weighted) | **0.594** |
| Nodes with w > 0.7 and s > 0.8 | 19 (strong foundation) |
| Nodes with energy > 0.4 | 2 (CRL1505, gut-lung narrative — design tension) |

### Information Architecture

The GA encodes information across **3 spatial axes**:

1. **Horizontal (x-axis):** Disease-to-health transition (left = pathology, right = clinical resolution)
2. **Vertical (y-axis):** Mechanism depth within bronchial tissue (lumen at top, muscle at bottom)
3. **Evidence axis:** Bar length in right panel (P32 channel, Stevens beta = 1.0)

This dual-spatial + quantitative architecture is the fundamental design innovation — it allows 4 products to be compared simultaneously on evidence strength AND mechanistic target.

---

## Section 2: Channel Scoring

### Overall Coverage Assessment

| Category | Score | Assessment |
|----------|-------|------------|
| **Structural zones** | 0.85 | Excellent — three-panel layout is clear, reading direction natural |
| **Product encoding** | 0.78 | Good — color hue for identity + bar length for evidence |
| **Immune cell encoding** | 0.55 | Moderate — labeled but visually undifferentiated |
| **Mechanism boxes** | 0.60 | Moderate — text-heavy, low pre-attentive encoding |
| **Evidence hierarchy** | 0.88 | Excellent — bar length is the optimal P32 channel |
| **Narrative flow** | 0.75 | Good — left-to-right progression, but implicit (no arrows) |
| **Weighted Overall** | **0.72** | Above average for the domain |

### Strengths (Channels Well Covered)

| Rank | Channel | Usage | Effectiveness |
|------|---------|-------|---------------|
| 1 | **Bar LENGTH (P32)** | Evidence hierarchy (18/5/1/Pre bars) | 0.95 — Stevens beta 1.0, optimal |
| 2 | **Spatial position (x)** | Disease-to-health macro narrative | 0.90 — left-to-right reading exploited |
| 3 | **Spatial position (y)** | Mechanism depth within bronchus | 0.85 — vertical position = tissue layer |
| 4 | **Color HUE** | Product identity (blue/teal/violet/green) | 0.80 — categorical, max discriminability |
| 5 | **Containment** | Spatial belonging (bronchus > layers > products) | 0.85 — Gestalt common region |
| 6 | **Icon shape** | Mechanism metaphor (shield/staple/helix/bridge) | 0.75 — metaphorical encoding |

### Gaps (Channels Poorly Covered)

| Rank | Channel | Issue | Current Score |
|------|---------|-------|---------------|
| 1 | **Cognitive load** | 40 nodes mapped; visual density likely exceeds 5s scan budget | Not managed |
| 2 | **Figure-ground** | No explicit contrast ratio specification for key elements | Not managed |
| 3 | **Text density** | 4 mechanism box labels + immune cell labels + product names + cascade steps = likely >30 words | CRITICAL |
| 4 | **Visual hierarchy levels** | At least 5 levels: panels > bronchus > tissue layers > cells > labels | Exceeds 3-level target |
| 5 | **Directional cues** | No arrows from problem (left) to solution (right) panel | Absent |
| 6 | **Info-noise ratio** | Immune cell labels (6 types) compete for attention with product names (4) and mechanisms (4) | Unaudited |

### Per-Node Breakdown

| Node | Weight | Stability | w*s | Visual Channels Used | Assessment |
|------|--------|-----------|-----|---------------------|------------|
| Bronchus (center) | 1.00 | 1.00 | 1.00 | Spatial position, containment, gradient, texture | Anchor element |
| OM-85 | 1.00 | 0.95 | 0.95 | Color, icon, bar length, position, label | Best-encoded product |
| 18 RCTs | 1.00 | 0.95 | 0.95 | Bar length, label, position | Strongest evidence |
| Fracture narrative | 0.95 | 0.90 | 0.86 | Left-to-right gradient, spatial transition | Implicit but powerful |
| Evidence hierarchy | 0.90 | 1.00 | 0.90 | Bar length (P32), vertical order | Optimal encoding |
| IgA/IgG | 0.85 | 0.90 | 0.77 | Antibody icons, labels, B Cell arrow | Well-connected |
| Pathological cascade | 0.80 | 1.00 | 0.80 | Sequential arrows, labels | Clear but text-heavy |
| PMBL | 0.65 | 0.80 | 0.52 | Color, icon, bar length, position | Adequate |
| MV130 | 0.35 | 0.50 | 0.18 | Color, icon, bar length, position | Underweight (proportional to evidence) |
| CRL1505 | 0.15 | 0.20 | 0.03 | Color, bridge icon, bar length | Weakest but visually distinctive (boundary breach) |
| Mechanism boxes (x4) | 0.60 | 0.83 | 0.50 | Text labels, position | Text-heavy, no pre-attentive signal |
| Immune cells (x6) | 0.49 | 1.00 | 0.49 | Labels, position within bronchus | Labeled but undifferentiated visually |

---

## Section 3: Recommendations

### Priority 1: CRITICAL — Reduce Text Density

| Property | Value |
|----------|-------|
| **Channel** | Cognitive load / Text density |
| **Current encoding** | ~50+ words across mechanism boxes, immune cell labels, cascade steps, product names, evidence labels, title |
| **Recommended encoding** | Reduce to 30 words max. Merge mechanism boxes into icon-based encoding. Use color coding instead of text labels for immune cells |
| **Expected delta-S9b** | +15-25% (text reduction directly improves 5-second scan completion rate) |
| **Specific action** | Remove mechanism box text labels. Replace with 4 icons color-coded to their respective products. The mechanism information is already encoded spatially by product position in the bronchus |

### Priority 2: HIGH — Reduce Visual Hierarchy Levels

| Property | Value |
|----------|-------|
| **Channel** | Visual hierarchy levels |
| **Current encoding** | 5+ levels: panels > bronchus > tissue layers > immune cells > labels |
| **Recommended encoding** | Cap at 3 levels: (1) Three-panel structure, (2) Bronchus with products, (3) Evidence bars. Merge immune cells into tissue layer background |
| **Expected delta-S9b** | +10-15% (fewer levels = faster scan path through GA) |
| **Specific action** | Remove individual immune cell labels. Instead, use color-coded dots or icons without text. The cell types are secondary information — the mechanism boxes already summarize them |

### Priority 3: HIGH — Add Directional Flow Cues

| Property | Value |
|----------|-------|
| **Channel** | Directional cues (arrows, visual flow) |
| **Current encoding** | None — relies on implicit Z-pattern left-to-right reading |
| **Recommended encoding** | Subtle directional arrow or gradient from left panel to center to right panel |
| **Expected delta-S9b** | +5-10% (ensures narrative order is perceived even at thumbnail scale) |
| **Specific action** | Add a thin green arrow from the pathological cascade (left) through the bronchus (center) to the clinical data bars (right). This makes the disease-to-evidence narrative explicit |

### Priority 4: MEDIUM — Strengthen Figure-Ground for Evidence Bars

| Property | Value |
|----------|-------|
| **Channel** | Figure-ground segregation |
| **Current encoding** | Bar chart in right panel — assumed figure but contrast ratio unspecified |
| **Recommended encoding** | Ensure WCAG 4.5:1 contrast ratio for all evidence bars against background. Add subtle shadow or outline |
| **Expected delta-S9b** | +5-8% at thumbnail scale (bars become visible at 200px width) |
| **Specific action** | Audit the bar chart at 50% zoom. If OM-85 bar is not immediately distinguishable from PMBL bar at that scale, increase color saturation difference or add border |

### Priority 5: MEDIUM — Encode Evidence Uncertainty on CRL1505

| Property | Value |
|----------|-------|
| **Channel** | Color luminance / edge sharpness |
| **Current encoding** | CRL1505 bar is identical in style to other bars, just shorter |
| **Recommended encoding** | Use dashed outline or lower opacity (40%) for the CRL1505 bar to visually encode "preclinical = uncertain" |
| **Expected delta-S9b** | +3-5% (viewers will correctly infer evidence quality hierarchy without reading labels) |
| **Specific action** | Make CRL1505 bar outline dashed (stroke-dasharray: 4 2) and reduce fill opacity to 0.4. This uses the luminance channel (Stevens beta 0.9) to encode uncertainty |

### Priority 6: LOW — Audit Color Accessibility

| Property | Value |
|----------|-------|
| **Channel** | Color hue discriminability |
| **Current encoding** | Blue (#2563EB), Teal (#0D9488), Violet (#7C3AED), Green (#059669) |
| **Recommended encoding** | Test with deuteranopia/protanopia simulation. Blue-violet pair may merge |
| **Expected delta-S9b** | +2-5% for 8% of male viewers |
| **Specific action** | Run the palette through a Coblis or Color Oracle simulator. If teal and green merge under deuteranopia, add pattern differentiation (hatching on one, solid on the other) |

---

## Section 4: Predicted Performance

### Expected S9b Range

| Metric | Value | Notes |
|--------|-------|-------|
| **Current estimated S9b** | 55-65% | Based on channel coverage analysis |
| **Post-recommendation S9b** | 70-80% | If priorities 1-3 implemented |
| **Theoretical maximum** | 85-90% | With all 6 recommendations implemented |

### Comparison with Batch Average (47 GAs)

| Benchmark | This GA | Batch Mean | Batch Median | Position |
|-----------|---------|------------|--------------|----------|
| **Information nodes** | 40 | 22 | 18 | Top 10% (high complexity) |
| **Evidence bar presence** | Yes (P32) | 15% of GAs | — | Top 15% |
| **Dual-axis spatial encoding** | Yes | 8% of GAs | — | Top 8% |
| **Text word count** | ~50+ | 35 | 28 | Bottom 30% (too many words) |
| **Visual hierarchy levels** | 5+ | 3.2 | 3 | Bottom 20% (too complex) |
| **Estimated S9b** | 55-65% | 47% | 42% | **Above average** |

### Domain Leaderboard Position

This GA ranks **above the 47-GA batch average** due to its use of the P32 bar-length channel for evidence hierarchy and its innovative dual-axis bronchial cross-section design. However, it is penalized by:

1. **Text density** exceeding the 30-word budget
2. **Visual complexity** with 40 mapped nodes competing for 5-second attention
3. **Absent directional cues** relying on implicit reading patterns

**Estimated percentile: 65th-75th** among scored GAs.

---

## Section 5: System 2 Predictions

### System 1 Survivors (High Visual Salience — Perceived in 5s Scroll)

These nodes will likely be perceived during a rapid 5-second scroll, relying on pre-attentive visual processing:

| Node | Why It Survives | Salience Driver |
|------|-----------------|-----------------|
| **Bronchial cross-section** | Largest visual element, central position, unique anatomical shape | Area (60% canvas), position (center), figure-ground |
| **Evidence bar chart** | High-contrast bars on right panel, length encoding (P32) | Length, position on common scale, color |
| **Sick child illustration** | Human figure triggers face/body detection circuits (~150ms) | Social signal, emotional valence |
| **OM-85 bar (longest)** | Dominant bar length in evidence chart | Length dominance, color contrast |
| **Left-to-right gradient** | Red-to-green color transition across canvas | Color temperature, spatial extent |
| **Product color coding** | 4 distinct hues create categorical popout | Pre-attentive color hue popout |

### System 2 Nodes (Require Deliberate Viewing — >5s)

These nodes carry critical information but will NOT be perceived during a quick scroll. They require deliberate, conscious reading:

| Node | Why It Requires System 2 | Information Risk |
|------|-------------------------|------------------|
| **Mechanism boxes (x4)** | Text labels only — no pre-attentive encoding. Requires reading | HIGH: The "why" of each product is invisible in 5s |
| **Individual immune cell labels** | Small text, densely packed within bronchus. 6 labels competing | MEDIUM: Cell type information lost at scroll speed |
| **RCT count labels** | "18 RCTs", "5 RCTs" etc. require reading the exact numbers | MEDIUM: Viewers see bar proportions but not exact counts |
| **CRL1505 "Preclinique" label** | Smallest bar + text label — bottom of visual hierarchy | HIGH: The weakest evidence status is easy to miss |
| **Pathological cascade steps** | 5-step sequential text in left panel | MEDIUM: Viewers see "problem" zone but not the steps |
| **Title text** | 9 words at top — requires conscious reading | LOW: Title is conventional position, may get a fixation |
| **Th1/Th2 balance** | Small element within lamina propria, no text at this scale | HIGH: Key immunological concept entirely missed |
| **Gut-lung bridge arc** | Novel visual element but unconventional = requires interpretation | MEDIUM: Seen but not understood without System 2 |

### Predicted System Delta

| Metric | Estimate |
|--------|----------|
| **System 1 capture rate** | 6-8 of 40 nodes (~17%) perceived in 5s |
| **System 2 capture rate** | 15-20 of 40 nodes (~42%) perceived with deliberate viewing (30s) |
| **delta_system (S1 vs S2)** | **25 percentage points** |
| **Information loss at scroll** | ~83% of mapped information vectors |

### Interpretation

The GA has a **large System 1/System 2 gap**. This is characteristic of mechanism-heavy scientific GAs that prioritize completeness over scannability. The core tension: this GA contains enough information to replace reading the abstract (high value), but most of that information requires System 2 processing to extract (low accessibility).

**Key insight:** The evidence hierarchy (bar chart) is the most efficiently encoded element and will survive scroll. The mechanism-of-action information (the scientific substance) is almost entirely System 2-dependent. This means the GA effectively communicates "which product has the most evidence" but NOT "how each product works."

**Recommendation:** If the primary audience is clinicians/researchers who will spend >10s, the current design is appropriate. If the primary audience is journal TOC browsers (5s scan), priorities 1-3 from Section 3 must be implemented to shift mechanism information into System 1 channels.

---

## Appendix: Visual Channel Inventory

| # | Channel | Information Encoded | Stevens Beta | Used? |
|---|---------|-------------------|-------------|-------|
| 1 | Bar length (P32) | Evidence hierarchy | 1.0 | YES |
| 2 | Position on common scale | Evidence ranking | 1.0 | YES |
| 3 | Spatial position (x) | Disease-health transition | n/a (spatial) | YES |
| 4 | Spatial position (y) | Mechanism depth | n/a (spatial) | YES |
| 5 | Color hue | Product identity | Categorical | YES |
| 6 | Color temperature | Zone valence (red/green) | Emotional | YES |
| 7 | Containment | Spatial belonging | Gestalt | YES |
| 8 | Icon shape | Mechanism metaphor | Categorical | YES |
| 9 | Icon size | Visual prominence | ~0.7 | YES |
| 10 | Boundary breach | Novelty (CRL1505 bridge) | Attention capture | YES |
| 11 | Human figure | Patient state | Social channel | YES |
| 12 | Text labels | Exact values | System 2 only | YES |
| 13 | Arrow direction | Cascade flow | Directional | YES (partial) |
| 14 | Tissue thickness | Remodeling severity | Length | YES |
| 15 | Cell integrity | Barrier health | Pattern | YES |
| 16 | Luminance | Evidence certainty | 0.9 | NO |
| 17 | Figure-ground | Element visibility | Gestalt | NOT MANAGED |
| 18 | Directional cues | Panel flow | Navigational | NO |
| 19 | Cognitive load | Scan budget | Compound | NOT MANAGED |
| 20 | Visual density | Whitespace ratio | Compound | NOT MANAGED |

**Used:** 15 of 20 mapped channels (75%)
**Unused high-value:** 5 channels (cognitive load, figure-ground, directional cues, luminance for uncertainty, visual density)

---

*Generated by GLANCE Recommendation Engine | SciSense | 2026-03-25*
*Graph: 40 nodes, 60 links | Visual channels: 15/20 active | Estimated S9b: 55-65%*
