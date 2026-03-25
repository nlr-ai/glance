"""GLANCE scoring engine — S9a/S9b/S9c auto-scoring.

Mathematical model: S2b_Mathematics.md

S9a scoring is handled entirely by semantic embedding (semantic.py).
The score_s9a function here is a passthrough stub that always returns False.
"""

from config_loader import get_constant

# ── Configurable constants ────────────────────────────────────────────────
# Loaded from config.yaml 'constants' section. See docs/SEMANTIC_SCORING.md
# "Constant Audit" for classification and rationale.

RT2_FAST_SLOW_MS = get_constant("rt2_fast_slow_ms", 3000)
RT2_HESITANT_LOST_MS = get_constant("rt2_hesitant_lost_ms", 8000)


def score_s9a(q1_text: str, keywords: list[str] | None = None) -> bool:
    """S9a: participant identifies the subject.

    STUB — always returns False. Actual S9a scoring is performed by
    semantic.score_s9a_semantic() in semantic.py, which uses embedding
    cosine similarity against multi-level reference texts.

    This function is kept for backward compatibility with callers that
    still pass keywords. The keywords parameter is ignored.
    """
    return False


def score_s9b(q2_choice: str, correct_product: str) -> bool:
    """S9b: participant identifies the best-documented product.
    PASS if choice matches correct answer."""
    if not q2_choice or not correct_product:
        return False
    return q2_choice.strip().lower() == correct_product.strip().lower()


def score_s9c(q3_choice: str) -> bool:
    """S9c: participant expresses change in perception/practice.
    PASS if answer is affirmative (boolean for backward compat)."""
    if not q3_choice:
        return False
    return q3_choice.strip().lower() in ("oui", "yes", "probablement", "probably")


def score_s9c_graduated(q3_choice: str) -> float:
    """S9c graduated scoring per S2b_Mathematics.md section 2.

    Returns:
        1.0 for "yes"/"oui"/"probablement"/"probably"
        0.5 for "need_more_data"/"besoin de plus de données"/"need_more"/"besoin"
        0.0 for "no"/"non" or empty/unknown

    Phenomenon: ordinal scale {0, 0.5, 1} maps the 3-level
    actionability response (S2b_Mathematics.md section 2).
    """
    if not q3_choice:
        return 0.0
    choice = q3_choice.strip().lower()
    # Phenomenon: 1.0 = full actionability (S2b_Mathematics.md section 2)
    if choice in ("oui", "yes", "probablement", "probably"):
        return 1.0
    # Phenomenon: 0.5 = partial actionability — "need more data" is scientifically
    # honest, not a failure (S2b_Mathematics.md section 2)
    if choice in ("need_more_data", "need_more", "besoin de plus de données",
                   "besoin de plus de donnees", "besoin", "besoin de voir le repo"):
        return 0.5
    return 0.0


def score_glance_composite(s9a: float, s9b: float, s9c: float) -> float:
    """Composite score per S2b_Mathematics.md section 7.

    Score_GLANCE = (0.2 * S9a) + (0.5 * S9b) + (0.3 * S9c)

    All inputs should be 0.0 or 1.0 for S9a/S9b (boolean cast to float),
    and 0.0/0.5/1.0 for S9c (graduated).

    Returns: float in [0, 1]

    Phenomenon: weights 0.2/0.5/0.3 are defined by S2b_Mathematics.md section 7.
    S9b (hierarchy) at 0.5 because it is the primary validation metric.
    S9c (actionability) at 0.3 because it is the end goal.
    S9a (recall) at 0.2 because free-recall is inherently noisy.
    Citation: S2b_Mathematics.md section 7, "Ponderation".
    """
    # Phenomenon: GLANCE composite weights (S2b_Mathematics.md section 7)
    return (0.2 * float(s9a)) + (0.5 * float(s9b)) + (0.3 * float(s9c))


def classify_speed_accuracy(s9b_pass: bool, q2_time_ms: int) -> str:
    """Speed-Accuracy Tradeoff per S2b_Mathematics.md section 3.

    Threshold: RT2_FAST_SLOW_MS (default 3000ms, from config.yaml).
    Returns one of: "fast_right", "slow_right", "fast_wrong", "slow_wrong"
    """
    fast = (q2_time_ms or 0) < RT2_FAST_SLOW_MS
    correct = bool(s9b_pass)
    if correct and fast:
        return "fast_right"
    if correct and not fast:
        return "slow_right"
    if not correct and fast:
        return "fast_wrong"
    return "slow_wrong"


def classify_rt2(median_rt2_ms: float) -> str:
    """RT2 fluency classification per S2b_Mathematics.md section 3.

    Thresholds from config.yaml: RT2_FAST_SLOW_MS and RT2_HESITANT_LOST_MS.
    Returns: "fluent" (<fast_slow), "hesitant" (fast_slow..hesitant_lost), "lost" (>hesitant_lost)
    """
    if median_rt2_ms < RT2_FAST_SLOW_MS:
        return "fluent"
    if median_rt2_ms <= RT2_HESITANT_LOST_MS:
        return "hesitant"
    return "lost"


def score_test(q1_text, q2_choice, q3_choice, correct_product, keywords=None,
               ga_metadata=None, q1_input_mode="text"):
    """Score all three GLANCE criteria.

    S9a is scored via semantic embedding when ga_metadata is provided (contains
    semantic_references). Falls back to the stub (always False) otherwise.
    The keywords parameter is ignored — kept only for backward compatibility.

    When q1_input_mode is 'voice' and ga_metadata is available, sentence-level
    semantic filtering is applied before scoring to remove meta-talk noise.

    Returns dict with boolean passes, graduated s9c, composite, speed-accuracy,
    and voice filter outputs (q1_filtered_text, q1_filter_ratio) when applicable.
    """
    # S9a — semantic scoring if available, otherwise stub (False)
    s9a = False
    s9a_score = 0.0
    q1_filtered_text = None
    q1_filter_ratio = None

    if ga_metadata:
        try:
            from semantic import score_s9a_semantic, filter_voice_transcript
            filter_voice = (q1_input_mode == "voice")

            # Pre-filter voice transcripts and store the results
            if filter_voice:
                q1_filtered_text, q1_filter_ratio = filter_voice_transcript(
                    q1_text, ga_metadata
                )

            s9a_score, s9a = score_s9a_semantic(
                q1_text, ga_metadata, filter_voice=filter_voice
            )
        except (ImportError, Exception):
            # semantic.py not available or model not loaded — degrade gracefully
            pass

    s9b = score_s9b(q2_choice, correct_product)
    s9c_pass = score_s9c(q3_choice)
    s9c_score = score_s9c_graduated(q3_choice)
    glance = score_glance_composite(float(s9a), float(s9b), s9c_score)
    return {
        "s9a": s9a,
        "s9a_score": s9a_score,
        "s9b": s9b,
        "s9c": s9c_pass,
        "s9c_score": s9c_score,
        "glance_score": glance,
        "q1_filtered_text": q1_filtered_text,
        "q1_filter_ratio": q1_filter_ratio,
    }
