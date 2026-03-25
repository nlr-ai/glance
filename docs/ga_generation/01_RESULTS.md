# Results — GA Generation V2

## R1: From Paper to GA
Given a paper abstract + key data, produce a Graphical Abstract where every visual element is traceable to a specific claim in the paper.

**Measurement:** Each GA narrative traces to a paper claim. 0 inventions (narratives without paper source). 0 critical omissions (paper claims with no narrative).

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
