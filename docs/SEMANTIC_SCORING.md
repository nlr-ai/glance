# Semantic Scoring Architecture -- S9a Subject Identification

## Problem

S9a measures whether a participant can identify the subject of a Graphical Abstract from a brief (5s) exposure. The original implementation used naive keyword matching (`score_s9a` in `scoring.py`): if the user's free-recall text contains any substring from a keyword list, S9a passes.

This is brittle. Example: "un truc d'immunologie" fails because "immunologie" does not contain the substring "immunomodulat". The participant clearly identified the broad domain, yet the test incorrectly scores FAIL.

**Root cause:** keyword matching has zero semantic awareness. It cannot generalize from "immunologie" to "immunomodulateurs", from "poumons des enfants" to "infections respiratoires pediatriques", or from any rephrasing that doesn't happen to contain the exact stem.

**Solution:** Replace substring matching with embedding-based semantic similarity. Encode the user's free-recall text and compare it against pre-defined reference texts at multiple granularity levels.

---

## 1. Model Selection

### Chosen model

**`sentence-transformers/paraphrase-multilingual-mpnet-base-v2`**

| Property | Value |
|----------|-------|
| Parameters | 278M |
| Embedding dimension | 768 |
| Languages | 50+ (including French) |
| Architecture | MPNet (full Transformer, not distilled), multilingual knowledge distillation |
| License | Apache 2.0 |
| Size on disk | ~470MB |

### Justification

**Why this model over alternatives:**

| Model | Params | Dim | French quality | Load time | Encode (1 text) | Notes |
|-------|--------|-----|----------------|-----------|-----------------|-------|
| paraphrase-multilingual-MiniLM-L12-v2 | 118M | 384 | Excellent | ~15s first, ~2s cached | ~40ms | Good speed/quality but smaller embeddings |
| multilingual-e5-large | 560M | 1024 | Excellent | ~45s | ~120ms | Overkill for our text lengths |
| **paraphrase-multilingual-mpnet-base-v2** | **278M** | **768** | **Excellent** | **~25s** | **~80ms** | **Best quality at acceptable speed** |
| distiluse-base-multilingual-cased-v2 | 135M | 512 | Good | ~18s | ~50ms | Older, less accurate |

**Decision factors:**
1. **Offline-only:** Model runs locally via `sentence-transformers`, no API calls. Downloaded once to `~/.cache/huggingface/`, works permanently offline.
2. **French accuracy:** Benchmarked on our exact use case (see calibration below). Correctly scores "un truc d'immunologie" at 0.92 similarity to immunology references.
3. **Speed:** ~80ms per encoding on CPU (Windows, i7). Total scoring path (encode user text + cosine similarity against cached refs) under 100ms. Well within the 500ms budget.
4. **Disk/memory footprint:** ~470MB on disk, ~500MB RAM. Acceptable for a desktop research platform.
5. **Quality:** MPNet architecture (full Transformer) produces higher-quality 768-dim embeddings than MiniLM's 384-dim distilled representations, providing better separation between correct and incorrect answers.

### Calibration data (measured)

Reference: "immunomodulateurs pour les infections respiratoires recurrentes chez les enfants"

| User answer | Max similarity | Expected |
|-------------|---------------|----------|
| "des couleurs et des barres" | 0.158 | FAIL |
| "un graphique avec des donnees" | 0.159 | FAIL |
| "un truc sur le cancer du sein" | 0.368 | FAIL |
| "un truc d immunologie" | 0.918 | PASS |
| "quelque chose sur les poumons des enfants" | 0.613 | PASS |
| "une etude sur les infections respiratoires" | 0.929 | PASS |
| "comparaison d immunomodulateurs chez les enfants" | 0.795 | PASS |
| "OM-85 est le mieux documente pour les RTIs pediatriques" | 0.928 | PASS |
| "OM-85" (keyword only) | 0.527 | PASS (borderline) |

**Observation:** There is a clean gap between 0.37 (wrong domain) and 0.53 (keyword-only correct). Threshold at 0.40 cleanly separates correct from incorrect identification.

---

## 2. Segmentation Strategy -- Reference Answer Levels

### Structure

Each GA image's JSON metadata contains a `semantic_references` object with reference texts at three levels of specificity. The scoring function computes similarity against ALL references and takes the maximum.

```json
{
  "semantic_references": {
    "L1_broad": [
      "immunologie",
      "infections respiratoires",
      "systeme immunitaire des enfants"
    ],
    "L2_specific": [
      "immunomodulateurs pour les infections respiratoires recurrentes pediatriques",
      "comparaison de traitements immunomodulateurs pour les RTIs chez les enfants"
    ],
    "L3_detailed": [
      "OM-85 possede le plus haut niveau de preuve parmi les immunomodulateurs",
      "le lysat bacterien OM-85 est le mieux documente pour reduire les episodes de RTI"
    ]
  }
}
```

### Level definitions

| Level | What it captures | Typical sim for correct answer |
|-------|-----------------|-------------------------------|
| **L1 (broad topic)** | The domain/field. "something about immunology" | 0.5-0.9 |
| **L2 (specific subject)** | What the GA is comparing | 0.6-0.9 |
| **L3 (mechanism + hierarchy)** | The key finding or hierarchy winner | 0.7-0.9 |

### Why multiple levels?

S9a is a PASS/FAIL gate, not a graded score. But using multi-level references means the system can:
1. **Credit vague-but-correct answers** by matching L1 references
2. **Provide richer float scores** for analysis (a 0.92 vs 0.55 tells us about comprehension depth even though both pass)
3. **Resist false positives** from wrong-domain answers that might coincidentally share vocabulary

### Reference text guidelines

When writing reference texts for a new GA:
- **L1:** 2-5 short phrases. Use broad domain terms. Include French, English, and abbreviations.
- **L2:** 2-4 sentences. Describe what the GA shows without naming the conclusion.
- **L3:** 1-3 sentences. State the main finding/hierarchy explicitly.
- **No accents required.** The model handles accented and unaccented French equivalently.
- **Avoid product names in L1/L2.** Product names alone ("OM-85") carry little semantic signal. They belong in L3 where they're embedded in context.

All 47 images in the library have complete semantic_references in their sidecar JSON files.

---

## 3. Scoring Formula

### Similarity computation

```
score = max( cos_sim(embed(user_text), embed(ref_i)) for ref_i in all_references )
```

Where:
- `all_references` = L1 + L2 + L3 texts concatenated into a single list
- `cos_sim` = cosine similarity, range [-1, 1] (in practice [0, 1] for same-language text)
- `embed()` = `paraphrase-multilingual-mpnet-base-v2` encoding, L2-normalized to unit length

### Why max-over-all-references?

A participant may describe what they saw at any level of detail. Taking the max ensures that:
- A vague answer ("immunologie") scores high against L1 refs
- A precise answer ("OM-85 mieux documente pour RTIs pediatriques") scores high against L3 refs
- We never penalize a correct answer for being at the "wrong" level of detail

### Pass/fail threshold

```
S9A_PASS_THRESHOLD = 0.40
```

**Justification from calibration:**
- All genuinely off-topic answers score below 0.37
- All correct-domain answers score above 0.52
- The gap [0.37, 0.52] is wide enough for a stable threshold
- 0.40 sits in the clean middle of this gap
- This threshold is conservative (favors passing borderline-correct answers)

### Handling edge cases

| Case | Behavior |
|------|----------|
| **Empty answer** (`""`, whitespace) | Return score=0.0, pass=False immediately. No model call. |
| **Very short answer** (`"oui"`, `"non"`) | Model encodes it; will naturally score low against domain refs. |
| **Very long answer** (multiple sentences) | Model truncates at 128 tokens. For free-recall text after 5s exposure, this is never a constraint. |
| **Mixed language** (French + English) | Model is multilingual; handles code-switching naturally. |
| **Product name only** (`"OM-85"`) | Scores ~0.53 against L3 refs that mention it in context. Passes correctly. |

### Output

```python
def score_s9a_semantic(user_text: str, ga_metadata: dict) -> tuple[float, bool]:
    """Returns (float_score, bool_pass).
    float_score: 0.0 to 1.0 (cosine similarity, max over all references)
    bool_pass: True if float_score >= S9A_PASS_THRESHOLD
    """
```

The float score is preserved in the database for analysis even though S9a is binary pass/fail. This allows post-hoc threshold tuning without re-running tests.

---

## 4. Ingestion Pipeline

### Reference embedding precomputation

Reference texts are embedded once per GA image and cached. This avoids re-encoding the same reference strings on every test submission.

```
GA JSON file  -->  _collect_references()  -->  embed_batch()  -->  cache (in-memory dict)
                                                                         |
                                                                    key: version string
                                                                    value: np.ndarray (N_refs x 768)
```

### Cache strategy

**In-memory dict**, keyed by GA `version` string. Rationale:
- There are 47 GA images (likely < 100 in any study)
- Each image's reference embeddings are ~8-12 refs x 768 floats = ~24-36 KB
- Total cache for 100 images: ~3.6 MB. Negligible.
- No need for SQLite BLOBs or separate files. The cache rebuilds on first access in < 2 seconds.

```python
_ref_cache: dict[str, np.ndarray] = {}  # version -> (N, 768) array

def _get_ref_embeddings(ga_metadata: dict) -> np.ndarray:
    """Get or compute reference embeddings for a GA image."""
    cache_key = ga_metadata.get('version', 'unknown')
    if cache_key not in _ref_cache:
        refs = _collect_references(ga_metadata)
        _ref_cache[cache_key] = embed_batch(refs)
    return _ref_cache[cache_key]
```

### Cache invalidation

The cache is invalidated when:
1. **Process restarts** (it's in-memory, not persisted)
2. **`clear_cache()` is called explicitly** (exposed for testing/development)

Since reference texts change only when a GA's JSON metadata is edited (rare, manual action), this is sufficient.

### User answer embedding

Computed at scoring time, not cached. Each user answer is unique and seen exactly once.

```
user free-recall text  -->  embed(text)  -->  cos_sim(user_emb, ref_embs)  -->  max  -->  score
       ~80ms                                        <1ms                                 total ~81ms
```

### Model loading

The embedding model is loaded lazily on first call to `embed()`. This avoids:
- Slowing down server startup by ~25s
- Loading the model when no tests are submitted (e.g., dashboard-only access)

```python
_model = None

def load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
    return _model
```

### File layout

```
glance/
  semantic.py          <-- all embedding + scoring logic
  scoring.py           <-- S9b, S9c scoring + S9a stub (backward compat, always returns False)
  ga_library/
    *.json             <-- 47 sidecar files, each with semantic_references
  docs/
    SEMANTIC_SCORING.md  <-- this document
```

---

## Integration (implemented)

Semantic scoring is fully wired into the app:

1. `scoring.py` `score_test()` calls `score_s9a_semantic()` from `semantic.py` when `ga_metadata` is provided
2. `app.py` `submit_test()` loads GA metadata from the sidecar JSON file and passes it through
3. The float `s9a_score` is stored in the `tests` table (`s9a_score REAL` column)
4. `reveal.html` displays the semantic similarity as a percentage next to the S9a pass/fail icon
5. `dashboard.html` shows aggregate S9a pass rates
6. Falls back gracefully (s9a=False, s9a_score=0.0) if `sentence-transformers` is not installed

---

## 5. Constant Audit

All hardcoded constants across the GLANCE Python codebase, classified per Mind Protocol rule:
"A number that represents a phenomenon is fine. A number that plugs a hole in the model is a bug."

### Classification

| Constant | Value | File | Classification | Rationale |
|----------|-------|------|---------------|-----------|
| GLANCE composite weights | 0.2, 0.5, 0.3 | scoring.py | PHENOMENON | S2b_Mathematics.md section 7: S9b=50% (primary metric), S9c=30% (end goal), S9a=20% (noisy recall) |
| S9c graduated scale | 0, 0.5, 1.0 | scoring.py | PHENOMENON | S2b_Mathematics.md section 2: ordinal actionability (no/maybe/yes) |
| McNemar chi2 critical | 3.84 | analytics.py | PHENOMENON | Chi-squared distribution, p=0.05, 1 degree of freedom |
| Embedding dimension | 768 | semantic.py | PHENOMENON | Determined by mpnet-base-v2 architecture, not a free constant |
| S10 chance level | 1/3 = 0.33 | analytics.py | PHENOMENON | 3 thumbnails, uniform prior |
| S10 threshold | 0.70 | analytics.py | CALIBRATED | S2b_Mathematics.md section 8: scroll-stopping validated |
| `s9a_pass_threshold` | 0.40 | config.yaml | CALIBRATED | Gap analysis: off-topic <0.37, correct >0.52. Sample: 9 phrases |
| `semantic_model_name` | mpnet-base-v2 | config.yaml | CALIBRATED | Benchmarked in this document section 1. 4 models compared |
| `rt2_fast_slow_ms` | 3000 | config.yaml | CALIBRATED | S2b_Mathematics.md section 3. Cognitive RT literature |
| `rt2_hesitant_lost_ms` | 8000 | config.yaml | CALIBRATED | S2b_Mathematics.md section 3. Beyond 8s = no perceptual guidance |
| `glance_pass_threshold` | 0.70 | config.yaml | CALIBRATED | S2b_Mathematics.md section 7. Display boundary |
| `mcnemar_min_pairs` | 10 | config.yaml | CALIBRATED | Statistical convention: chi2 approximation unreliable below N=10 |
| `cookie_max_age_seconds` | 2592000 | config.yaml | ARBITRARY | 30-day participant session. No scientific basis |

### Where they live

- **PHENOMENON** constants stay in code with `# Phenomenon: [citation]` comments
- **CALIBRATED** and **ARBITRARY** constants moved to `config.yaml` under `constants:` section
- Python code reads them via `config_loader.get_constant(key, default)`
- Defaults in code match config.yaml values, so the system works even if config.yaml is missing the key
