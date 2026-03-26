# Objectives — GA Generation V2

## Goals

1. **Paper-faithful** — The GA represents the paper's argument, not just its data. Every element encodes a real claim IN CONTEXT — the claim's role in the paper's narrative (evidence for X, mechanism of Y) is encoded visually.
2. **AI-informed, SVG-delivered** — Gen AI explores the visual space. The deliverable is always parametric SVG with exact control. When multiple AI variants are generated, select the one that best preserves the paper's narrative structure, not just channel coverage.
3. **Channel-driven convergence** — The delta between AI reference and SVG object is measured per information channel, not per pixel.
4. **Self-improving library** — Each GA produced expands the object library and the channel ontology.
5. **Auditable end-to-end** — Paper claim → narrative → visual element → channel → reader attention. Every link queryable.
5a. **Narrative fidelity auditable** — Each narrative's meaning must be verifiable against the paper. The visual encoding of a narrative must survive round-trip: paper → GA → reader interpretation → same narrative.

## Non-Goals

- NOT photo-realistic rendering (SVG parametric is the deliverable)
- NOT a general-purpose illustration tool (scientific GAs only)
- NOT dependent on any single gen AI model (the AI is the teacher, the SVG is the student)
- NOT manual design (the human chooses what to communicate, the system designs how)

## Trade-offs

- **Expressivity vs Control** — Gen AI has unlimited expressivity but no precision. SVG has precision but limited expressivity. The hybrid uses AI for ideation and SVG for delivery.
- **Speed vs Fidelity** — Quick wireframe (1 min, low fidelity) vs polished GA (10 min, high fidelity). The system should support both.
- **Generic vs Domain-specific** — Objects are learned per domain (immunology cells ≠ climate charts). The library grows domain by domain.
