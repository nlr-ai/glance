# Sync — GA Generation V2

## Current State: SPECIFIED (not implemented)

Version: 0.0 — Full spec. No code.

## What Exists Already

| Component | Status | Where |
|-----------|--------|-------|
| Parametric compositor | DONE (mission-specific) | `missions/immunomodulator/scripts/compose_ga_v15.py` |
| vec_lib drawing primitives | DONE | `scripts/vec_lib.py` |
| Vision scorer (image → graph, enrichment mode) | DONE | `glance/vision_scorer.py` |
| Channel analyzer (70 channels) | DONE | `glance/channel_analyzer.py` |
| Reader sim | DONE | `glance/reader_sim.py` |
| Graph health | DONE | `glance/graph_health.py` |
| deepen() multi-resolution | DONE | `glance/deepen.py` |
| GA advisor (Gemini recommendations) | DONE | `glance/ga_advisor.py` |
| Auto-improve loop | DONE | `glance/ga_auto_improve.py` |
| Image generation (Ideogram/Gemini) | PARTIAL (MCP media tool) | mind-mcp |

## What Needs Building

### Phase 1: Paper → Claims (A1)
- [ ] `claim_extractor.py` — Gemini reads abstract → structured claims YAML
- [ ] Each claim: value, data family, priority, source sentence
- [ ] Link claims to narrative nodes

### Phase 2: Multi-Resolution Analysis (A2)
- [x] deepen() exists — recursively analyzes spaces
- [ ] AUTO-TRIGGER: deepen should run automatically after initial analysis
- [ ] Per-space channel analysis (channels on crops, not just full image)

### Phase 3: AI Reference Generation (A3)
- [ ] `reference_generator.py` — prompt builder from claims → gen AI
- [ ] Generate N variants per object/concept
- [ ] Analyze each variant (graph + channels)
- [ ] Build parameter space (PCA on channel vectors)

### Phase 4: Parametric Object Learning (A4)
- [ ] `object_learner.py` — AI variants → SVG parametric function
- [ ] Channel delta measurement (AI vs SVG)
- [ ] SVG implementation of discoverable channels (feTurbulence, patterns, etc.)
- [ ] Object library (`objects/` directory with learned objects)

### Phase 5: Layout Optimization (A5)
- [ ] `layout_optimizer.py` — hill climb on reader sim
- [ ] YAML layout → graph → sim → score → perturb → repeat
- [ ] 1000 iterations in <1 second

### Phase 6: Assembly + Validation (A6)
- [ ] `ga_assembler.py` — objects + layout → final SVG
- [ ] Validation pipeline: analyze + sim + channel check
- [ ] Audit chain document generation

### Phase 7: Web Integration
- [ ] `/create-ga` endpoint — abstract input → GA output
- [ ] Progress tracking (each step visible)
- [ ] Library browser (browse learned objects)

## Priority for Aurore's GA (this week)

1. **A1**: Extract claims from the immunomod manuscript → YAML spec
2. **A2**: Run multi-res analysis on V15 wireframe (deepen)
3. Skip A3-A4 for now — use existing compositor objects
4. **A5**: Optimize V15 layout via reader sim hill climb
5. **A6**: Validate + audit chain
6. Manual polish by Aurore in Illustrator

## Single-Graph Architecture

Each GA has exactly ONE graph row in the database. All tools (vision, channels, deepen, advise) merge into this single graph via `save_graph()` which handles deduplication and version tracking.

### Vision Enrichment Mode

`vision_scorer.py` has two prompt modes:

- **Fresh mode** (`VISION_PROMPT`): Used when no graph exists yet. Produces a complete L3 graph from scratch (spaces, narratives, things, links, metadata).
- **Enrichment mode** (`ENRICHMENT_PROMPT`): Used when a prior graph with nodes exists. Instructs Gemini to review the existing graph against the image, returning ONLY additions and corrections. The merge in `save_graph()` handles deduplication.

The mode is selected automatically based on whether `prior_graph` is a dict with nodes.

### Analysis Flow

```
Upload → vision (fresh) → deepen → channels → reader_sim → advise
                                                                ↓
                                              (swap image) → vision (enrich) → channels → reader_sim → advise
                                                                ↓
                                              (tool: vision) → vision (enrich) → merge
```

- **Initial upload** (`/analyze/submit`): Vision runs in fresh mode (no prior graph). Auto-improve background thread runs channels → reader_sim → advise (NOT vision again).
- **Swap image** (`/analyze/swap-image/{slug}`): Fetches existing graph, passes it as `prior_graph` to vision (enrichment mode). Then channels → reader_sim → advise.
- **Tool endpoint** (`/analyze/tool/vision/{slug}`): Always fetches `get_latest_graph()`. If a graph exists, passes it as `prior_graph` (enrichment mode). If not, fresh mode.
- **Batch analyze** (`/admin/batch-analyze`): Checks for existing graph per GA. Passes it as `prior_graph` if found.
- **Improve** (`/analyze/improve/{slug}`): Does NOT re-run vision. Runs advise on the latest graph.

### Key Invariant

Vision is only called in fresh mode ONCE per GA (at first upload or first analysis). Every subsequent vision call receives the existing graph and operates in enrichment mode — producing deltas, not full rebuilds.

## Changes Log

- 2026-03-26: Vision enrichment mode refactor. ENRICHMENT_PROMPT replaces vague "modify/extend" append. All app.py call sites verified: tool endpoint, swap-image, batch all pass existing graph. Auto-improve confirmed to NOT re-run vision.
- 2026-03-25: Full spec written (01-03, 05, 10). Architecture: AI as teacher, SVG as student. Channel delta convergence. Six data families. Multi-resolution analysis with per-space channel passes.
