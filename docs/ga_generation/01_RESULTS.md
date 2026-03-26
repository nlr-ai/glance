# Results — GA Generation V2

## R1: From Paper to GA — Fidelity

Given a paper abstract + key data, produce a Graphical Abstract where every visual element is traceable to a specific claim in the paper AND preserves the paper's narrative meaning and hierarchy.

### R1a: Structural Fidelity
Every GA narrative element traces to a paper claim. No inventions, no critical omissions.

**Measurement:** 0 inventions (narratives without paper source). 0 critical omissions (paper claims with no narrative).

### R1b: Semantic Fidelity
GA narrative meanings match the paper's claims — not just structural traceability, but semantic equivalence. A GA element that traces to a claim but distorts its meaning is a semantic infidelity.

**Measurement:** For each GA narrative ↔ paper claim pair, embedding similarity >= 0.85 (using the same `paraphrase-multilingual-mpnet-base-v2` model as S9a scoring). Any pair below 0.85 triggers manual review.

### R1c: Hierarchical Fidelity
If the paper establishes a hierarchy (A > B, treatment X outperforms Y, evidence level I vs II), the GA visual hierarchy must reflect the same ordering. Visual dominance (size, position, color intensity, emphasis) must match the paper's stated ordering.

**Measurement:** For each explicit hierarchy in the paper, the GA's visual encoding preserves the same direction. 0 hierarchy inversions (GA shows B > A when paper says A > B). 0 hierarchy flattening (GA shows A = B when paper says A > B).

## R2: Channel-Accurate Parametric Objects
Each visual object in the GA encodes the same information channels as a gen AI reference, but in parametric SVG.

**Measurement:** channel delta between AI reference and SVG object < 0.3 on all critical channels.

## R3: Optimized Layout
The layout parameters are optimized by hill climbing on the reader sim score.

**Measurement:** reader sim narrative coverage ≥ 80% after optimization.

## R4: Auditable Chain
Every pixel traces: paper claim → GA narrative → thing node → visual channel → reader attention → % transmitted.

**Measurement:** the chain is queryable in the graph. No broken links.

## R5: Reusable Object Library
Each object learned from AI variants joins a library, reusable across GAs.

**Measurement:** library grows with each GA produced. Objects have documented parameter ranges.

## R6: Channel Discovery
New visual channels discovered from AI variants are added to the ontology.

**Measurement:** channel catalog grows beyond the initial 70. Each new channel has: name, what it communicates, SVG implementation (if possible).

## R7: Context Preservation
After each generation, verify that the GA's narrative chain matches the paper's argument chain. The paper presents claims in a logical sequence (problem → method → evidence → conclusion). The GA must preserve this argument structure, not just isolated facts.

**Measurement:** `argument_chain_fidelity >= 0.95`. Computed as: extract the paper's argument chain (ordered list of claim nodes), extract the GA's narrative chain (ordered list of narrative nodes), measure alignment via pairwise semantic similarity of corresponding steps. A chain break (similarity < 0.85 at any step) or a reordering that changes the logical implication counts as a fidelity violation.
