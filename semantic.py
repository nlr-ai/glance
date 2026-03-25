"""GLANCE semantic scoring — embedding-based S9a subject identification.

Replaces naive keyword matching with cosine similarity against multi-level
reference texts. Uses paraphrase-multilingual-MiniLM-L12-v2 (118M params,
384-dim embeddings, 50+ languages including French).

Typical latency: ~40ms per scoring call (CPU, after model warmup).
See docs/SEMANTIC_SCORING.md for full architecture documentation.
"""

from __future__ import annotations

import logging
import numpy as np

from config_loader import get_constant

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────
# Calibrated constants loaded from config.yaml; see docs/SEMANTIC_SCORING.md.

MODEL_NAME = get_constant("semantic_model_name",
                          "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
S9A_PASS_THRESHOLD = get_constant("s9a_pass_threshold", 0.40)

# Embedding dimension is determined by the model, not a free constant.
# Hardcoded here because it must match the model architecture.
_MODEL_DIM_LOOKUP = {
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": 768,
}
EMBEDDING_DIM = _MODEL_DIM_LOOKUP.get(MODEL_NAME, 384)

# ── Module-level state (lazy-initialized) ────────────────────────────────

_model = None
_ref_cache: dict[str, np.ndarray] = {}


# ── Model loading ────────────────────────────────────────────────────────

def load_model():
    """Lazy-load the sentence-transformers embedding model.

    First call downloads the model (~250MB) if not cached in
    ~/.cache/huggingface/. Subsequent calls return the cached instance.
    Load time: ~15s first run, ~2s from cache.
    """
    global _model
    if _model is not None:
        return _model

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "sentence-transformers is required for semantic scoring. "
            "Install with: pip install sentence-transformers"
        ) from e

    logger.info("Loading embedding model: %s", MODEL_NAME)
    _model = SentenceTransformer(MODEL_NAME)
    logger.info("Model loaded. Embedding dim: %d", _model.get_sentence_embedding_dimension())
    return _model


# ── Embedding functions ──────────────────────────────────────────────────

def embed(text: str) -> np.ndarray:
    """Encode a single text string into an embedding vector.

    Args:
        text: Input text (any language supported by the model).

    Returns:
        numpy array of shape (EMBEDDING_DIM,), L2-normalized.
    """
    model = load_model()
    # encode() returns (1, dim) for a single string; squeeze to (dim,)
    return model.encode(text, normalize_embeddings=True)


def embed_batch(texts: list[str]) -> np.ndarray:
    """Encode multiple texts into embedding vectors.

    Args:
        texts: List of input texts.

    Returns:
        numpy array of shape (len(texts), EMBEDDING_DIM), L2-normalized.
    """
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
    model = load_model()
    return model.encode(texts, normalize_embeddings=True)


# ── Reference text extraction ───────────────────────────────────────────

def _collect_references(ga_metadata: dict) -> list[str]:
    """Extract all reference texts from GA metadata, across all levels.

    Expects ga_metadata to contain a 'semantic_references' dict with keys
    'L1_broad', 'L2_specific', 'L3_detailed', each mapping to a list of
    strings. Missing keys are silently skipped.

    Falls back to title + description if semantic_references is absent.
    """
    sem_refs = ga_metadata.get("semantic_references")

    if sem_refs and isinstance(sem_refs, dict):
        refs = []
        for level_key in ("L1_broad", "L2_specific", "L3_detailed"):
            level_texts = sem_refs.get(level_key, [])
            if isinstance(level_texts, list):
                refs.extend(t for t in level_texts if isinstance(t, str) and t.strip())
        if refs:
            return refs

    # Fallback: construct references from title and description
    fallback = []
    if ga_metadata.get("title"):
        fallback.append(ga_metadata["title"])
    if ga_metadata.get("description"):
        fallback.append(ga_metadata["description"])
    if fallback:
        logger.warning(
            "No semantic_references in GA metadata (version=%s). "
            "Falling back to title+description.",
            ga_metadata.get("version", "?"),
        )
        return fallback

    logger.error("GA metadata has no semantic_references, title, or description.")
    return []


def _get_ref_embeddings(ga_metadata: dict) -> np.ndarray:
    """Get or compute cached reference embeddings for a GA image.

    Cache key is the GA version string. Cache lives in-memory for the
    lifetime of the process.

    Returns:
        numpy array of shape (N_refs, EMBEDDING_DIM), L2-normalized.
        Empty array (0, EMBEDDING_DIM) if no references found.
    """
    cache_key = ga_metadata.get("version", "unknown")
    if cache_key in _ref_cache:
        return _ref_cache[cache_key]

    refs = _collect_references(ga_metadata)
    if not refs:
        empty = np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
        _ref_cache[cache_key] = empty
        return empty

    logger.info(
        "Computing reference embeddings for GA version=%s (%d refs)",
        cache_key, len(refs),
    )
    ref_embs = embed_batch(refs)
    _ref_cache[cache_key] = ref_embs
    return ref_embs


# ── Scoring functions ────────────────────────────────────────────────────

def score_semantic(user_text: str, references: list[str]) -> float:
    """Compute semantic similarity between user text and reference texts.

    Args:
        user_text: The participant's free-recall answer.
        references: List of reference strings to compare against.

    Returns:
        Float in [0.0, 1.0]: maximum cosine similarity between user_text
        and any reference. Returns 0.0 for empty inputs.
    """
    if not user_text or not user_text.strip():
        return 0.0
    if not references:
        return 0.0

    user_emb = embed(user_text)  # shape: (dim,)
    ref_embs = embed_batch(references)  # shape: (N, dim)

    # Cosine similarity (embeddings are already L2-normalized)
    similarities = ref_embs @ user_emb  # shape: (N,)
    return float(np.max(similarities))


def filter_voice_transcript(raw_transcript: str, ga_metadata: dict,
                            noise_threshold: float = 0.15) -> tuple[str, float]:
    """Filter meta-talk from voice transcript, keep only recall-relevant sentences.

    Voice transcripts contain ~80% meta-talk ("est-ce que ça marche", "trop bien")
    and ~20% actual recall ("comparaison matricielle de mélanome"). The embedding
    of the full transcript is diluted by noise, producing artificially low S9a scores.

    This function splits the transcript into sentences, computes cosine similarity
    of each against the GA's semantic references, and keeps only sentences above
    the noise threshold.

    Args:
        raw_transcript: Raw speech-to-text output.
        ga_metadata: GA image metadata containing semantic_references.
        noise_threshold: Minimum cosine similarity for a sentence to be kept.
            Default 0.15 is deliberately low — it filters obvious meta-talk
            (sim ~0.02-0.08) while keeping even tangentially relevant recall.

    Returns:
        Tuple of (filtered_text, filter_ratio):
            filtered_text: Space-joined kept sentences. Falls back to raw
                transcript if nothing passes the threshold.
            filter_ratio: len(kept) / len(total_sentences). A cognitive style
                metric — low ratio = lots of meta-talk, high ratio = focused recall.
    """
    if not raw_transcript or not raw_transcript.strip():
        return "", 0.0

    # Split by sentence boundaries (periods, question marks, commas for speech)
    import re
    sentences = re.split(r'[.!?\n]+', raw_transcript)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]

    if not sentences:
        return raw_transcript, 1.0

    # Get reference embeddings
    ref_embs = _get_ref_embeddings(ga_metadata)
    if ref_embs.shape[0] == 0:
        return raw_transcript, 1.0

    # Score each sentence against references
    kept = []
    for sentence in sentences:
        sent_emb = embed(sentence)
        sim = float(np.max(ref_embs @ sent_emb))
        if sim >= noise_threshold:
            kept.append(sentence)

    filtered = " ".join(kept) if kept else raw_transcript  # fallback to raw if nothing passes
    ratio = len(kept) / len(sentences)

    logger.info(
        "Voice filter: %d/%d sentences kept (ratio=%.2f, threshold=%.2f)",
        len(kept), len(sentences), ratio, noise_threshold,
    )
    return filtered, ratio


def score_s9a_semantic(
    user_text: str,
    ga_metadata: dict,
    threshold: float = S9A_PASS_THRESHOLD,
    filter_voice: bool = False,
) -> tuple[float, bool]:
    """Score S9a (subject identification) using semantic similarity.

    Compares the participant's free-recall text against multi-level
    reference texts defined in the GA image's metadata. Takes the maximum
    similarity across all reference levels.

    Args:
        user_text: The participant's free-recall answer (Q1).
        ga_metadata: The GA image's full JSON metadata dict, expected to
            contain a 'semantic_references' field with L1/L2/L3 texts.
        threshold: Cosine similarity threshold for PASS. Default 0.40.
        filter_voice: When True, apply filter_voice_transcript() before
            scoring. Use this for voice transcripts to remove meta-talk
            that dilutes the embedding.

    Returns:
        Tuple of (score, passed):
            score: float in [0.0, 1.0], maximum cosine similarity
            passed: bool, True if score >= threshold
    """
    if not user_text or not user_text.strip():
        return 0.0, False

    scoring_text = user_text
    if filter_voice:
        filtered, _ratio = filter_voice_transcript(user_text, ga_metadata)
        if filtered and filtered.strip():
            scoring_text = filtered

    ref_embs = _get_ref_embeddings(ga_metadata)
    if ref_embs.shape[0] == 0:
        logger.error("No reference embeddings available. Cannot score.")
        return 0.0, False

    user_emb = embed(scoring_text)  # shape: (dim,)

    # Cosine similarity (both sides L2-normalized, so dot product = cosine)
    similarities = ref_embs @ user_emb  # shape: (N_refs,)
    score = float(np.max(similarities))
    passed = score >= threshold

    logger.debug(
        "S9a semantic: text=%r score=%.3f threshold=%.2f pass=%s filter_voice=%s",
        scoring_text[:80], score, threshold, passed, filter_voice,
    )
    return score, passed


# ── Cache management ─────────────────────────────────────────────────────

def clear_cache():
    """Clear the reference embedding cache.

    Call this after editing semantic_references in GA metadata files,
    or when you want to force recomputation.
    """
    _ref_cache.clear()
    logger.info("Reference embedding cache cleared.")


def cache_info() -> dict:
    """Return cache diagnostics.

    Returns:
        Dict with 'entries' (int), 'keys' (list of cached version strings),
        and 'model_loaded' (bool).
    """
    return {
        "entries": len(_ref_cache),
        "keys": list(_ref_cache.keys()),
        "model_loaded": _model is not None,
    }
