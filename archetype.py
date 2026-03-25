"""GLANCE Archetype Classifier — diagnostic archetypes for Graphical Abstracts.

Assigns a descriptive archetype to each GA based on its GLANCE score profile
and distortion signatures. Rule-based classification (not ML) — designed to
give researchers an immediate, intuitive diagnosis of their GA's strengths
and weaknesses.

7 archetypes: cristallin, spectacle, tresor_enfoui, encyclopedie,
              desequilibre, embelli, fantome.
"""

import math

# ── Archetype definitions ────────────────────────────────────────────────

ARCHETYPES = {
    "cristallin": {
        "name_fr": "Cristallin",
        "name_en": "Crystal Clear",
        "emoji": "\U0001f48e",
        "description_fr": "Le GA parfait \u2014 capte l'attention et transmet le message int\u00e9gralement.",
        "description_en": "The perfect GA \u2014 captures attention and fully transmits the message.",
        "signature": "S10\u2191 S9b\u2191 Drift\u2193 Warp\u2193",
        "recommendation_fr": "Maintenez ce niveau de qualit\u00e9. Ce GA peut servir de r\u00e9f\u00e9rence pour votre domaine.",
        "recommendation_en": "Maintain this quality level. This GA can serve as a reference for your domain.",
        "color": "#059669",
        "color_bg": "rgba(5, 150, 105, 0.12)",
        "color_label": "emerald",
    },
    "spectacle": {
        "name_fr": "Spectacle",
        "name_en": "Eye Candy",
        "emoji": "\U0001f3aa",
        "description_fr": "Visuellement saisissant mais le message ne passe pas \u2014 l'attention est capt\u00e9e sans transf\u00e9rer l'information.",
        "description_en": "Visually striking but the message doesn't get through \u2014 attention captured without information transfer.",
        "signature": "S10\u2191 S9b\u2193 Drift\u2191",
        "recommendation_fr": "R\u00e9duisez les \u00e9l\u00e9ments d\u00e9coratifs. Renforcez l'encodage des donn\u00e9es (barres > surfaces).",
        "recommendation_en": "Reduce decorative elements. Strengthen data encoding (bars > areas).",
        "color": "#7c3aed",
        "color_bg": "rgba(124, 58, 237, 0.12)",
        "color_label": "purple",
    },
    "tresor_enfoui": {
        "name_fr": "Tr\u00e9sor Enfoui",
        "name_en": "Hidden Gem",
        "emoji": "\U0001f48e\U0001faa8",
        "description_fr": "Le contenu est riche et bien structur\u00e9, mais invisible au scroll \u2014 il faut s'arr\u00eater pour comprendre.",
        "description_en": "Rich, well-structured content that's invisible at scroll speed \u2014 requires deliberate viewing.",
        "signature": "S10\u2193 S2\u2191 Drift\u2191\u2191",
        "recommendation_fr": "Augmentez la saillance visuelle : couleurs plus vives, taille des \u00e9l\u00e9ments cl\u00e9s, contraste figure-fond.",
        "recommendation_en": "Increase visual saliency: brighter colors, larger key elements, better figure-ground contrast.",
        "color": "#d97706",
        "color_bg": "rgba(217, 119, 6, 0.12)",
        "color_label": "amber",
    },
    "encyclopedie": {
        "name_fr": "Encyclop\u00e9die",
        "name_en": "Encyclopedia",
        "emoji": "\U0001f4da",
        "description_fr": "Trop de texte \u2014 rien ne survit en 5 secondes de scroll. L'information est noy\u00e9e dans les mots.",
        "description_en": "Too much text \u2014 nothing survives 5 seconds of scrolling. Information drowned in words.",
        "signature": "Words\u2191\u2191 S9b\u2193",
        "recommendation_fr": "R\u00e9duisez \u00e0 30 mots maximum. Remplacez le texte par des encodages visuels (barres, positions, tailles).",
        "recommendation_en": "Reduce to 30 words maximum. Replace text with visual encodings (bars, positions, sizes).",
        "color": "#2563eb",
        "color_bg": "rgba(37, 99, 235, 0.12)",
        "color_label": "blue",
    },
    "desequilibre": {
        "name_fr": "D\u00e9s\u00e9quilibr\u00e9",
        "name_en": "Lopsided",
        "emoji": "\u2696\ufe0f",
        "description_fr": "Un \u00e9l\u00e9ment domine tout le GA \u2014 les autres informations sont invisibles. Hi\u00e9rarchie visuelle d\u00e9form\u00e9e.",
        "description_en": "One element dominates \u2014 other information is invisible. Distorted visual hierarchy.",
        "signature": "Warp\u2191\u2191",
        "recommendation_fr": "R\u00e9\u00e9quilibrez la hi\u00e9rarchie visuelle. Donnez plus d'espace et de poids aux donn\u00e9es sous-repr\u00e9sent\u00e9es.",
        "recommendation_en": "Rebalance the visual hierarchy. Give more space and weight to under-represented data.",
        "color": "#ea580c",
        "color_bg": "rgba(234, 88, 12, 0.12)",
        "color_label": "orange",
    },
    "embelli": {
        "name_fr": "Embelli",
        "name_en": "Polished",
        "emoji": "\u2728",
        "description_fr": "Communique efficacement... mais le message est biais\u00e9. La hi\u00e9rarchie per\u00e7ue ne refl\u00e8te pas les donn\u00e9es r\u00e9elles.",
        "description_en": "Communicates effectively... but the message is biased. Perceived hierarchy doesn't match actual data.",
        "signature": "S9b\u2191 + Spin d\u00e9tect\u00e9",
        "recommendation_fr": "V\u00e9rifiez que l'encodage visuel est proportionnel aux effect sizes r\u00e9els. Axes non tronqu\u00e9s, \u00e9chelles lin\u00e9aires.",
        "recommendation_en": "Verify that visual encoding is proportional to actual effect sizes. No truncated axes, linear scales.",
        "color": "#db2777",
        "color_bg": "rgba(219, 39, 119, 0.12)",
        "color_label": "pink",
    },
    "fantome": {
        "name_fr": "Fant\u00f4me",
        "name_en": "Ghost",
        "emoji": "\U0001f47b",
        "description_fr": "N'existe pas visuellement \u2014 le lecteur scrolle sans m\u00eame le remarquer. Scroll-through total.",
        "description_en": "Visually non-existent \u2014 the reader scrolls right past. Complete scroll-through.",
        "signature": "S10\u2193 S9b\u2193 S2\u2193",
        "recommendation_fr": "Refonte compl\u00e8te n\u00e9cessaire. Commencez par un \u00e9l\u00e9ment d'accroche visuelle fort, puis structurez l'information autour.",
        "recommendation_en": "Complete redesign needed. Start with a strong visual hook, then structure information around it.",
        "color": "#6b7280",
        "color_bg": "rgba(107, 114, 128, 0.12)",
        "color_label": "gray",
    },
}

# Ideal score profiles for distance-based fallback classification
_ARCHETYPE_PROFILES = {
    "cristallin":    {"s10": 0.85, "s9b": 0.85, "s2_coverage": 0.7, "drift": 0.1, "warp": 0.2, "word_norm": 0.3},
    "spectacle":     {"s10": 0.75, "s9b": 0.25, "s2_coverage": 0.3, "drift": 0.6, "warp": 0.4, "word_norm": 0.3},
    "tresor_enfoui": {"s10": 0.25, "s9b": 0.4,  "s2_coverage": 0.7, "drift": 0.6, "warp": 0.4, "word_norm": 0.4},
    "encyclopedie":  {"s10": 0.3,  "s9b": 0.3,  "s2_coverage": 0.4, "drift": 0.4, "warp": 0.5, "word_norm": 0.9},
    "desequilibre":  {"s10": 0.4,  "s9b": 0.4,  "s2_coverage": 0.4, "drift": 0.5, "warp": 1.2, "word_norm": 0.4},
    "embelli":       {"s10": 0.6,  "s9b": 0.7,  "s2_coverage": 0.5, "drift": 0.3, "warp": 0.4, "word_norm": 0.4},
    "fantome":       {"s10": 0.15, "s9b": 0.15, "s2_coverage": 0.15,"drift": 0.5, "warp": 0.5, "word_norm": 0.5},
}


# ── Classification logic ─────────────────────────────────────────────────

def classify_ga(scores: dict) -> dict:
    """Classify a GA into an archetype based on its GLANCE scores.

    Args:
        scores: dict with keys:
            - s10: float 0-1 (saliency, stream mode — typically avg_s9a or
              a dedicated saliency metric; use avg_s9a as proxy)
            - s9b: float 0-1 (hierarchy comprehension)
            - s2_coverage: float 0-1 (System 2 coverage)
            - drift: float (avg delta_system across nodes, 0-1+)
            - warp: float (sigma/mu of node coverage, 0-2+)
            - word_count: int
            - spin_detected: bool (optional, default False)

    Returns:
        dict with:
            - archetype: str (key into ARCHETYPES)
            - confidence: float 0-1
            - method: str ("rule" or "distance")
            - archetype_info: dict (full archetype definition)
    """
    s10 = float(scores.get("s10", 0.0))
    s9b = float(scores.get("s9b", 0.0))
    s2_coverage = float(scores.get("s2_coverage", 0.0))
    drift = float(scores.get("drift", 0.0))
    warp = float(scores.get("warp", 0.0))
    word_count = int(scores.get("word_count", 0))
    spin_detected = bool(scores.get("spin_detected", False))

    archetype = None
    confidence = 0.0
    method = "rule"

    # Priority order matters -- first match wins

    # 1. Cristallin: high saliency, high hierarchy, low distortion
    if s10 >= 0.7 and s9b >= 0.7 and drift < 0.3 and warp < 0.5:
        archetype = "cristallin"
        # Confidence scales with how far above thresholds
        confidence = min(1.0, (s10 - 0.5) * 2 * (s9b - 0.5) * 2)

    # 2. Fantome: nothing works
    elif s10 < 0.3 and s9b < 0.3 and s2_coverage < 0.3:
        archetype = "fantome"
        confidence = min(1.0, (1.0 - s10) * (1.0 - s9b) * (1.0 - s2_coverage))

    # 3. Encyclopedie: text overload
    elif word_count > 50 and s9b < 0.5:
        archetype = "encyclopedie"
        # More words + lower s9b = higher confidence
        word_excess = min(1.0, (word_count - 30) / 70.0)
        confidence = min(1.0, word_excess * (1.0 - s9b))

    # 4. Embelli: spin detected
    elif spin_detected:
        archetype = "embelli"
        confidence = 0.7  # spin detection itself is the signal

    # 5. Desequilibre: extreme warp
    elif warp > 1.0:
        archetype = "desequilibre"
        confidence = min(1.0, (warp - 0.5) / 1.5)

    # 6. Spectacle: eye-catching but no message transfer
    elif s10 >= 0.5 and s9b < 0.4 and drift > 0.4:
        archetype = "spectacle"
        confidence = min(1.0, s10 * (1.0 - s9b) * drift)

    # 7. Tresor enfoui: rich content, invisible at scroll speed
    elif s10 < 0.4 and s2_coverage > 0.5 and drift > 0.3:
        archetype = "tresor_enfoui"
        confidence = min(1.0, (1.0 - s10) * s2_coverage * drift)

    # Fallback: find closest archetype by Euclidean distance on score profile
    if archetype is None:
        archetype, confidence = _classify_by_distance(
            s10, s9b, s2_coverage, drift, warp, word_count
        )
        method = "distance"

    confidence = round(max(0.05, min(1.0, confidence)), 3)

    return {
        "archetype": archetype,
        "confidence": confidence,
        "method": method,
        "archetype_info": ARCHETYPES[archetype],
    }


def _classify_by_distance(s10, s9b, s2_coverage, drift, warp, word_count):
    """Fallback classification by Euclidean distance to ideal archetype profiles.

    Normalizes word_count to 0-1 range (cap at 100 words) for fair comparison.
    Returns (archetype_key, confidence).
    """
    word_norm = min(1.0, word_count / 100.0)
    ga_profile = {
        "s10": s10,
        "s9b": s9b,
        "s2_coverage": s2_coverage,
        "drift": drift,
        "warp": min(2.0, warp) / 2.0,  # normalize warp to 0-1
        "word_norm": word_norm,
    }

    best_key = "fantome"
    best_dist = float("inf")
    distances = {}

    for key, profile in _ARCHETYPE_PROFILES.items():
        # Normalize profile warp for distance calc
        p = dict(profile)
        p["warp"] = min(2.0, p["warp"]) / 2.0

        dist = math.sqrt(sum(
            (ga_profile[dim] - p[dim]) ** 2
            for dim in ga_profile
        ))
        distances[key] = dist
        if dist < best_dist:
            best_dist = dist
            best_key = key

    # Confidence: inverse of distance, scaled so dist=0 -> 1.0, dist=2 -> 0.1
    max_possible_dist = math.sqrt(len(ga_profile))  # theoretical max ~ 2.45
    confidence = max(0.05, 1.0 - (best_dist / max_possible_dist))

    return best_key, confidence


# ── Vision metadata approximation ────────────────────────────────────────

# Chart type -> approximate drift potential
_CHART_DRIFT = {
    "pie": 0.6,
    "scatter": 0.4,
    "heatmap": 0.5,
    "infographic": 0.5,
    "mixed": 0.4,
    "other": 0.4,
    "bar": 0.2,
    "line": 0.25,
}


def classify_from_vision_metadata(metadata: dict) -> dict:
    """Approximate archetype classification from Gemini Vision metadata.

    Used when no user test data exists yet. Provides a "predicted" archetype
    based on structural properties observable from the image alone.

    Args:
        metadata: dict with keys from vision_scorer.py:
            - word_count: int
            - hierarchy_clear: bool
            - chart_type: str

    Returns:
        Same format as classify_ga(), with method="vision_approximation".
    """
    word_count = int(metadata.get("word_count", 0))
    hierarchy_clear = bool(metadata.get("hierarchy_clear", False))
    chart_type = str(metadata.get("chart_type", "other")).lower()

    # Approximate s9b from hierarchy_clear
    s9b_approx = 0.7 if hierarchy_clear else 0.3

    # Approximate drift from chart type
    drift_approx = _CHART_DRIFT.get(chart_type, 0.4)

    # Approximate s10: higher word count -> lower saliency (text competes
    # with visuals for pre-attentive processing)
    if word_count <= 20:
        s10_approx = 0.6
    elif word_count <= 40:
        s10_approx = 0.45
    else:
        s10_approx = 0.25

    # s2_coverage: assume moderate (unknown without test data)
    s2_approx = 0.4

    # warp: approximate from chart type (pie charts tend to warp more)
    warp_approx = 0.8 if chart_type == "pie" else 0.4

    scores = {
        "s10": s10_approx,
        "s9b": s9b_approx,
        "s2_coverage": s2_approx,
        "drift": drift_approx,
        "warp": warp_approx,
        "word_count": word_count,
        "spin_detected": False,
    }

    result = classify_ga(scores)
    result["method"] = "vision_approximation"
    result["approximated_scores"] = scores
    return result


def get_archetype_info(archetype_key: str) -> dict:
    """Return the full archetype definition for a given key.

    Returns the fantome archetype if key is not found (fail loud with
    a visible signal rather than silently returning nothing).
    """
    if archetype_key not in ARCHETYPES:
        return ARCHETYPES["fantome"]
    return ARCHETYPES[archetype_key]
