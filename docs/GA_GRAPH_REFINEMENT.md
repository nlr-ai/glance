# GLANCE GA — Graph Refinement Process

## What this is
The GA's information architecture expressed as an L3 graph. Each design element
is a node with physics dimensions. The graph is the single source of truth for
what the GA communicates.

## Refinement loop

1. **Map** — Every information vector becomes an L3 node (actor/moment/narrative/space/thing)
2. **Dimension** — Assign weight (importance), stability (confidence), energy (needs work)
3. **Link** — Connect nodes with relational dimensions (hierarchy, trust, friction, affinity, aversion)
4. **Contain** — Place nodes inside space nodes (zone_left, zone_right) with hierarchy:-1 links
5. **Identify tension** — High energy + low stability = unresolved. The graph shows what to fix.
6. **Design** — Marco translates the graph to visual elements. Each node = a visual element. Each link = a visual relationship.
7. **Test** — GLANCE protocol measures if the hierarchy was perceived (S9b). Data flows back to update stability.
8. **Iterate** — Stability grows with data. Energy drops when resolved. The graph converges.

## V2 changes (2026-03-25)

### 6 new nodes

| Node | Type | Why |
|------|------|-----|
| `space:ga:domain` | space | Overarching domain space for scientific visual communication. Contains both zones. |
| `thing:5_seconds` | thing | The 5-second exposure constraint. Critical design parameter GLANCE is built around. |
| `narrative:protocol` | narrative | The GLANCE testing methodology (stream mode, inertial scroll, S10 saillance). Distinct from thing:glance (the score). |
| `thing:comprehension_gap_data` | thing | Bredbenner 2019 (N=538): GAs rank 3rd out of 4 formats. The data point that anchors the gap. |
| `narrative:perceptual_science` | narrative | Cleveland & McGill + Stevens + MacEachren. Theoretical foundation for why spin works and why GLANCE measures what it measures. |
| `thing:open_source` | thing | Apache 2.0, GitHub repo. The reproducibility claim. |

### 6 new semantic links

| Link | Why |
|------|-----|
| `thing:vanity` -> `space:ga:zone_left` | Vanity metrics belong to the problem space (containment). |
| `thing:engagement` -> `thing:comprehension` | Direct disconnect link (polarity: -1). The core contradiction made explicit. |
| `narrative:spin` -> `thing:ga_thumbnail` | Spin deforms the thumbnail (friction: 0.8). |
| `actor:scisense` -> `narrative:protocol` | SciSense built the protocol (affinity: 0.9). |
| `space:ga:zone_left` -> `space:ga:zone_right` | The fracture link between zones (polarity: -1, hierarchy: 0). |
| `moment:6_rcts` -> `narrative:gap` | The evidence corpus supports the gap claim (trust: 0.85). |

### Dimension refinements

| Change | Before | After | Why |
|--------|--------|-------|-----|
| `narrative:gap` energy | 0.20 | 0.10 | The gap is well-established, not in flux. |
| `thing:glance` recency | 1.0 | 1.0 | Confirmed explicitly — GLANCE is the most recent node. |
| `thing:vanity` permanence | (absent) | 1.0 | Vanity metrics being useless is a permanent fact. |
| ALL nodes ambivalence | (some absent) | 0.0 | The GA has zero ambiguity. Now explicit on every node. |

### Structural improvements

- **Domain space** (`space:ga:domain`) as parent of both zones with containment links.
- **Evidence moments** (akl_2007, 6_rcts) and **actor** (scisense) contained in domain space (not zone-specific).
- **All new nodes** have containment links to their respective zones.
- **Every link** has a synthesis field.

### Graph size

- V1: 13 nodes, 19 links
- V2: 19 nodes, 38 links

## Current tensions (2026-03-25 V2)

| Node | Weight | Stability | Energy | Status |
|------|--------|-----------|--------|--------|
| thing:glance | 1.00 | 0.40 | 0.90 | CRITICAL — ≥80% is a target, not a result |
| thing:ga_thumbnail | 0.85 | 0.70 | 0.80 | OPEN — which GA to show? Loupe deformation? |
| narrative:spin | 0.50 | 0.65 | 0.75 | FUZZY — Vorland extrapolation not direct |
| narrative:protocol | 0.80 | 0.60 | 0.60 | ACTIVE — protocol under construction |
| thing:5_seconds | 0.65 | 0.85 | 0.15 | STABLE — well-grounded constraint |

## What stabilizes the graph
- **Data from crash test** (N=5-10) → thing:glance stability rises from 0.40 to 0.70+
- **Marco's visual execution** → thing:ga_thumbnail energy drops to 0.15
- **Stronger spin citation** or **reframe** → narrative:spin stability rises to 0.80+
- **Protocol finalization** → narrative:protocol energy drops, stability rises to 0.80+

## Invariants
- permanence = 1.0 on all spaces (the message is permanent scientific fact)
- ambivalence = 0.0 on ALL nodes (no ambiguity — problem is clear, solution is clear)
- hierarchy is the critical dimension (V7) — encoded by P32 (length)
- S9b measures hierarchy perception — graph and protocol are aligned
- Every node inside a space has a containment link (hierarchy: -1.0)
- Every link has a synthesis

## Files
- Graph: `data/glance_ga_graph.yaml`
- Math: `GLANCE_Mathematics.md`
- Paper: `GLANCE_Paper_Draft.md`
- Design spec: `GLANCE_GA_Design_Spec.md` (Marco's brief)
