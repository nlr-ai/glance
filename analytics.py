"""GLANCE analytics — aggregate statistics per S2b_Mathematics.md.

All formulas from sections 2-7 of the mathematical model.
"""

import math
import statistics

from scoring import classify_speed_accuracy, classify_rt2, score_glance_composite
from config_loader import get_constant

# ── Configurable constants ────────────────────────────────────────────────
MCNEMAR_MIN_PAIRS = get_constant("mcnemar_min_pairs", 10)

try:
    import numpy as np
    def _median(values):
        if not values:
            return 0.0
        return float(np.median(values))
except ImportError:
    from statistics import median as _stats_median
    def _median(values):
        if not values:
            return 0.0
        return float(_stats_median(values))


def compute_fluency_score(s9b_pass: bool, q2_time_ms: int) -> float:
    """Fluency = S9b / log(RT2). Fast correct > slow correct > wrong.

    Phenomenon: combines accuracy (binary) with reaction time (continuous)
    into a single continuous metric that rewards fast correct responses.
    Unlike binary S9b, this captures the *quality* of the correct answer —
    a fast correct response indicates stronger perceptual encoding than a
    slow correct response.

    Returns 0.0 for incorrect or missing data.
    """
    if not s9b_pass or not q2_time_ms or q2_time_ms <= 0:
        return 0.0
    return 1.0 / math.log(max(q2_time_ms, 100))  # avoid log(0)


def compute_cognitive_effort_index(s9a_score: float, filter_ratio: float,
                                   first_utterance_ms: int) -> dict:
    """Combines filter_ratio + latency into a cognitive effort metric.

    High effort = correct answer but low filter_ratio (lots of meta-talk)
    and/or high latency (slow recall).

    Phenomenon: meta-talk ratio (1 - filter_ratio) captures how much
    cognitive overhead the participant needed to formulate their answer.
    Latency captures how quickly the memory trace was accessible.
    Together they form a composite effort index.

    Args:
        s9a_score: Semantic similarity score (not used in computation,
                   kept for future correlation analysis).
        filter_ratio: Proportion of retained phrases after voice filtering
                      (q1_filter_ratio). None if text mode.
        first_utterance_ms: Time to first keystroke/utterance (ms).

    Returns:
        dict with effort_score (0=effortless, 1=maximum effort),
        components, and interpretation label.
    """
    effort = 0.0
    n_components = 0

    if filter_ratio is not None and filter_ratio > 0:
        effort += (1.0 - filter_ratio)  # more meta-talk = more effort
        n_components += 1

    if first_utterance_ms and first_utterance_ms > 0:
        effort += min(1.0, math.log(first_utterance_ms / 1000) / 3)  # normalize to 0-1
        n_components += 1

    avg_effort = (effort / n_components) if n_components > 0 else 0.0

    return {
        "effort_score": round(avg_effort, 3),
        "filter_ratio": filter_ratio,
        "latency_ms": first_utterance_ms,
        "interpretation": "effortless" if avg_effort < 0.3 else "moderate" if avg_effort < 0.6 else "laborious",
    }


def compute_aggregate_stats(tests: list[dict]) -> dict:
    """Compute aggregate metrics across a list of test dicts.

    Each test dict must have: s9a_pass, s9b_pass, s9c_score, q2_time_ms, glance_score.

    Returns:
        {
            "Taux_S9a": float,      # proportion S9a correct
            "Taux_S9b": float,      # proportion S9b correct
            "Score_S9c": float,     # mean graduated S9c
            "Mediane_RT2": float,   # median q2_time_ms
            "RT2_class": str,       # fluent/hesitant/lost
            "Score_GLANCE": float,     # mean composite score
            "N": int,
        }
    """
    n = len(tests)
    if n == 0:
        return {
            "Taux_S9a": 0.0,
            "Taux_S9b": 0.0,
            "Score_S9c": 0.0,
            "Mediane_RT2": 0.0,
            "RT2_class": "lost",
            "Score_GLANCE": 0.0,
            "N": 0,
        }

    taux_s9a = sum(1 for t in tests if t.get("s9a_pass")) / n
    taux_s9b = sum(1 for t in tests if t.get("s9b_pass")) / n
    score_s9c = sum(t.get("s9c_score", 0.0) or 0.0 for t in tests) / n

    rt2_values = [t["q2_time_ms"] for t in tests if t.get("q2_time_ms")]
    mediane_rt2 = _median(rt2_values)
    rt2_class = classify_rt2(mediane_rt2)

    score_glance = sum(t.get("glance_score", 0.0) or 0.0 for t in tests) / n

    # Fluency: S9b / log(RT2) — continuous metric per S2b_Mathematics.md section 3
    fluency_scores = [
        compute_fluency_score(bool(t.get("s9b_pass")), t.get("q2_time_ms", 0))
        for t in tests
    ]
    avg_fluency = sum(fluency_scores) / n

    # Cognitive effort: filter_ratio + latency composite
    effort_scores = []
    for t in tests:
        fr = t.get("q1_filter_ratio")
        lat = t.get("q1_first_keystroke_ms")
        if fr is not None or (lat and lat > 0):
            cei = compute_cognitive_effort_index(
                t.get("s9a_score", 0.0), fr, lat
            )
            effort_scores.append(cei["effort_score"])
    avg_effort = sum(effort_scores) / len(effort_scores) if effort_scores else None

    return {
        "Taux_S9a": round(taux_s9a, 4),
        "Taux_S9b": round(taux_s9b, 4),
        "Score_S9c": round(score_s9c, 4),
        "Mediane_RT2": round(mediane_rt2, 1),
        "RT2_class": rt2_class,
        "Score_GLANCE": round(score_glance, 4),
        "Avg_Fluency": round(avg_fluency, 4),
        "Avg_Effort": round(avg_effort, 3) if avg_effort is not None else None,
        "N": n,
    }


def compute_profile_quadrant(clinical_domain: str, data_literacy: str) -> str:
    """Map participant profile to one of 4 quadrants per S2b_Mathematics.md section 4.

    Axes:
        - Clinical expertise: high if clinical_domain in {pediatrician, gp, researcher_bio,
          Pédiatre, Médecin Généraliste, Chercheur Bio/Médical}
        - Data literacy: high if data_literacy in {published_author, tech_data,
          Auteur publié (peer-review), Profil Tech/Data}

    Returns one of: "Q1_public_naif", "Q2_tech", "Q3_clinicien", "Q4_clinicien_chercheur"
    """
    clinical_high_values = {
        "pediatrician", "gp", "researcher_bio",
        "pédiatre", "médecin généraliste", "chercheur bio/médical",
    }
    data_high_values = {
        "published_author", "tech_data",
        "auteur publié (peer-review)", "profil tech/data",
    }

    cd = (clinical_domain or "").strip().lower()
    dl = (data_literacy or "").strip().lower()

    clinical_high = cd in clinical_high_values
    data_high = dl in data_high_values

    if clinical_high and data_high:
        return "Q4_clinicien_chercheur"
    if clinical_high and not data_high:
        return "Q3_clinicien"
    if not clinical_high and data_high:
        return "Q2_tech"
    return "Q1_public_naif"


def compute_stats_by_quadrant(tests: list[dict], participants: list[dict] = None) -> dict:
    """Compute aggregate stats grouped by profile quadrant.

    Each test dict must have clinical_domain and data_literacy fields
    (from JOIN with participants).

    Returns: dict mapping quadrant string -> stats dict (same shape as compute_aggregate_stats).
    """
    buckets = {}
    for t in tests:
        q = compute_profile_quadrant(t.get("clinical_domain", ""), t.get("data_literacy", ""))
        buckets.setdefault(q, []).append(t)

    return {q: compute_aggregate_stats(ts) for q, ts in buckets.items()}


def compute_speed_accuracy_distribution(tests: list[dict]) -> dict:
    """Count tests in each speed-accuracy quadrant per S2b_Mathematics.md section 3.

    Returns: {"fast_right": int, "slow_right": int, "fast_wrong": int, "slow_wrong": int}
    """
    counts = {"fast_right": 0, "slow_right": 0, "fast_wrong": 0, "slow_wrong": 0}
    for t in tests:
        sa = t.get("speed_accuracy")
        if not sa:
            # Compute on the fly if not stored
            sa = classify_speed_accuracy(t.get("s9b_pass", False), t.get("q2_time_ms", 0))
        if sa in counts:
            counts[sa] += 1
    return counts


def compute_s10_rate(tests: list[dict]) -> dict:
    """Compute S10 saillance rate per S2b_Mathematics.md section 8.

    S10 = P(participant selects the GA cible among 3 thumbnails).
    Only applies to stream-mode tests where s10_hit is recorded.

    Chance level = 1/3 = 0.33. Threshold for scroll-stopping = >0.70.

    Returns:
        {
            "s10_rate": float,        # proportion of hits
            "n_stream": int,          # total stream tests with s10 data
            "n_hits": int,            # number of correct selections
            "s10_label": str,         # interpretation label
            "s10_x_s9b": float | None,  # S10 x S9b product (chain metric)
        }
    """
    stream_tests = [
        t for t in tests
        if t.get("exposure_mode") == "stream" and t.get("s10_hit") is not None
    ]
    n = len(stream_tests)
    if n == 0:
        return {
            "s10_rate": 0.0,
            "n_stream": 0,
            "n_hits": 0,
            "s10_label": "Pas de données stream",
            "s10_x_s9b": None,
        }

    n_hits = sum(1 for t in stream_tests if t.get("s10_hit"))
    s10_rate = n_hits / n

    if s10_rate > 0.70:
        label = "Scroll-stopping validé"
    elif s10_rate >= 0.33:
        label = "Pas plus mémorable que les distracteurs"
    else:
        label = "Activement ignoré (pire que le hasard)"

    # Compute S10 x S9b chain metric
    taux_s9b = sum(1 for t in stream_tests if t.get("s9b_pass")) / n
    s10_x_s9b = round(s10_rate * taux_s9b, 4)

    return {
        "s10_rate": round(s10_rate, 4),
        "n_stream": n,
        "n_hits": n_hits,
        "s10_label": label,
        "s10_x_s9b": s10_x_s9b,
    }


def compute_ab_delta(tests_control: list[dict], tests_vec: list[dict]) -> dict:
    """Compute A/B delta per S2b_Mathematics.md section 5.

    Delta_S9b = Taux_S9b(VEC) - Taux_S9b(control)

    Optional McNemar chi-squared if sufficient paired data.

    Returns:
        {
            "delta_s9b": float,
            "taux_s9b_control": float,
            "taux_s9b_vec": float,
            "n_control": int,
            "n_vec": int,
            "mcnemar_chi2": float | None,
            "mcnemar_significant": bool | None,  # at p=0.05 (chi2 > 3.84)
        }
    """
    n_ctrl = len(tests_control)
    n_vec = len(tests_vec)

    taux_ctrl = sum(1 for t in tests_control if t.get("s9b_pass")) / n_ctrl if n_ctrl else 0.0
    taux_vec = sum(1 for t in tests_vec if t.get("s9b_pass")) / n_vec if n_vec else 0.0
    delta = taux_vec - taux_ctrl

    result = {
        "delta_s9b": round(delta, 4),
        "taux_s9b_control": round(taux_ctrl, 4),
        "taux_s9b_vec": round(taux_vec, 4),
        "n_control": n_ctrl,
        "n_vec": n_vec,
        "mcnemar_chi2": None,
        "mcnemar_significant": None,
    }

    # McNemar requires paired data — match by participant_id
    ctrl_by_pid = {t["participant_id"]: bool(t.get("s9b_pass")) for t in tests_control if "participant_id" in t}
    vec_by_pid = {t["participant_id"]: bool(t.get("s9b_pass")) for t in tests_vec if "participant_id" in t}

    paired_pids = set(ctrl_by_pid.keys()) & set(vec_by_pid.keys())
    if len(paired_pids) >= MCNEMAR_MIN_PAIRS:
        # b = control correct, VEC incorrect
        # c = control incorrect, VEC correct
        b = sum(1 for pid in paired_pids if ctrl_by_pid[pid] and not vec_by_pid[pid])
        c = sum(1 for pid in paired_pids if not ctrl_by_pid[pid] and vec_by_pid[pid])

        if (b + c) > 0:
            chi2 = ((b - c) ** 2) / (b + c)
            result["mcnemar_chi2"] = round(chi2, 4)
            # Phenomenon: chi2 critical value 3.84 = chi-squared distribution
            # at p=0.05 with 1 degree of freedom (standard statistical threshold)
            result["mcnemar_significant"] = chi2 > 3.84

    return result


def compute_ab_fluency_delta(tests_control: list[dict], tests_vec: list[dict]) -> dict:
    """Compare fluency (S9b/log(RT2)) between control and VEC, not just binary S9b.

    Phenomenon: binary McNemar tests whether the *proportion* of correct answers
    differs, but loses information about *how fast* the correct answers were.
    Fluency = 1/log(RT2) for correct responses, 0 for incorrect, captures both
    accuracy and speed in a single continuous metric. This enables Wilcoxon
    signed-rank test (for paired data) or Mann-Whitney U (for unpaired),
    which have more statistical power than McNemar on continuous data.

    Returns:
        {
            "fluency_control": float,   # mean fluency for control group
            "fluency_vec": float,       # mean fluency for VEC group
            "fluency_delta": float,     # VEC - control
            "interpretation": str,      # human-readable label
        }
    """
    def fluency(t):
        if not t.get("s9b_pass") or not t.get("q2_time_ms"):
            return 0.0
        return 1.0 / math.log(max(t["q2_time_ms"], 100))

    f_control = [fluency(t) for t in tests_control]
    f_vec = [fluency(t) for t in tests_vec]

    mean_control = sum(f_control) / len(f_control) if f_control else 0
    mean_vec = sum(f_vec) / len(f_vec) if f_vec else 0

    return {
        "fluency_control": round(mean_control, 4),
        "fluency_vec": round(mean_vec, 4),
        "fluency_delta": round(mean_vec - mean_control, 4),
        "interpretation": "VEC faster+more accurate" if mean_vec > mean_control else "Control better or equal",
    }


# ── GA Detail analytics ────────────────────────────────────────────────


def get_ga_detail_stats(ga_image_id: int) -> dict:
    """Compute detailed aggregate stats for a single GA image.

    Queries all tests for this GA and computes:
    - avg/individual S9a, S9b, S9c, composite, fluency scores
    - S2 node coverage aggregates
    - speed-accuracy distribution
    - test count and timing

    Returns dict with all computed aggregates, safe for 0-test case.
    """
    from db import get_tests_for_image
    import json

    tests = get_tests_for_image(ga_image_id)
    n = len(tests)

    if n == 0:
        return {
            "n_tests": 0,
            "avg_s9a": 0.0,
            "avg_s9b": 0.0,
            "avg_s9c": 0.0,
            "avg_glance": 0.0,
            "avg_fluency": 0.0,
            "fluency_normalized": 0.0,
            "avg_s2_coverage": 0.0,
            "s2_node_means": {},
            "speed_dist": {"fast_right": 0, "slow_right": 0, "fast_wrong": 0, "slow_wrong": 0},
            "tests": [],
        }

    # S9a: use s9a_score (continuous) if available, else binary pass
    s9a_scores = [float(t.get("s9a_score") or 0.0) for t in tests]
    avg_s9a = sum(s9a_scores) / n

    # S9b: binary pass rate
    s9b_passes = [1 if t.get("s9b_pass") else 0 for t in tests]
    avg_s9b = sum(s9b_passes) / n

    # S9c: graduated score
    s9c_scores = [float(t.get("s9c_score") or 0.0) for t in tests]
    avg_s9c = sum(s9c_scores) / n

    # GLANCE composite
    glance_scores = [float(t.get("glance_score") or 0.0) for t in tests]
    avg_glance = sum(glance_scores) / n

    # Fluency
    fluency_scores = [
        compute_fluency_score(bool(t.get("s9b_pass")), t.get("q2_time_ms", 0))
        for t in tests
    ]
    avg_fluency = sum(fluency_scores) / n

    # Normalize fluency to 0-1 range for radar chart (max theoretical ~ 0.22 at 100ms)
    # Use 0.15 as practical max for normalization
    fluency_normalized = min(1.0, avg_fluency / 0.15) if avg_fluency > 0 else 0.0

    # Speed-accuracy distribution
    speed_dist = compute_speed_accuracy_distribution(tests)

    # S2 node coverage aggregates
    s2_coverages = []
    s2_node_aggregates = {}  # node_id -> list of scores across tests
    for t in tests:
        if t.get("s2_node_coverage"):
            try:
                cov = json.loads(t["s2_node_coverage"])
                from scoring import compute_system2_coverage
                s2_coverages.append(compute_system2_coverage(cov))
                for node_id, score in cov.items():
                    s2_node_aggregates.setdefault(node_id, []).append(score)
            except (json.JSONDecodeError, Exception):
                pass

    avg_s2_coverage = (sum(s2_coverages) / len(s2_coverages)) if s2_coverages else 0.0

    # Average per-node scores
    s2_node_means = {
        nid: sum(scores) / len(scores)
        for nid, scores in s2_node_aggregates.items()
    }

    return {
        "n_tests": n,
        "avg_s9a": round(avg_s9a, 4),
        "avg_s9b": round(avg_s9b, 4),
        "avg_s9c": round(avg_s9c, 4),
        "avg_glance": round(avg_glance, 4),
        "avg_fluency": round(avg_fluency, 4),
        "fluency_normalized": round(fluency_normalized, 4),
        "avg_s2_coverage": round(avg_s2_coverage, 4),
        "s2_node_means": s2_node_means,
        "speed_dist": speed_dist,
        "tests": tests,
    }


# ── Leaderboard analytics ──────────────────────────────────────────────


def get_leaderboard_data(domain_config: dict) -> dict:
    """Return leaderboard data: domain -> list of GA rankings.

    Each GA entry contains:
        ga_image_id, title, filename, domain, avg_glance, avg_s9b,
        n_tests, avg_s2_coverage

    Args:
        domain_config: dict from config.yaml["domains"] — used for labels.

    Returns:
        dict mapping domain_key -> {
            "label": str,
            "gas": list of GA dicts sorted by avg_glance desc,
            "n_gas": int,
            "n_tests": int,
            "top_score": float,
            "avg_score": float,
        }
    """
    from db import get_db
    import json

    db = get_db()

    # All GA images
    images = db.execute("SELECT * FROM ga_images ORDER BY id").fetchall()
    images = [dict(r) for r in images]

    # All tests with scores
    test_rows = db.execute(
        """SELECT ga_image_id,
                  glance_score,
                  s9b_pass,
                  s2_node_coverage
           FROM tests
           WHERE ga_image_id IS NOT NULL"""
    ).fetchall()
    db.close()

    # Build per-GA aggregates
    ga_stats = {}  # ga_image_id -> {scores, s9b_passes, s2_coverages}
    for t in test_rows:
        gid = t["ga_image_id"]
        if gid not in ga_stats:
            ga_stats[gid] = {"glance_scores": [], "s9b_passes": [], "s2_coverages": []}
        ga_stats[gid]["glance_scores"].append(t["glance_score"] or 0.0)
        ga_stats[gid]["s9b_passes"].append(1 if t["s9b_pass"] else 0)
        if t["s2_node_coverage"]:
            try:
                cov = json.loads(t["s2_node_coverage"])
                from scoring import compute_system2_coverage
                ga_stats[gid]["s2_coverages"].append(compute_system2_coverage(cov))
            except Exception:
                pass

    # Group images by domain
    domain_groups = {}
    for img in images:
        d = img["domain"]
        domain_groups.setdefault(d, []).append(img)

    result = {}
    for domain_key, imgs in domain_groups.items():
        label = domain_config.get(domain_key, {}).get("label", domain_key)
        gas = []
        for img in imgs:
            gid = img["id"]
            stats = ga_stats.get(gid)
            if stats and stats["glance_scores"]:
                avg_glance = sum(stats["glance_scores"]) / len(stats["glance_scores"])
                avg_s9b = sum(stats["s9b_passes"]) / len(stats["s9b_passes"])
                n_tests = len(stats["glance_scores"])
                avg_s2 = (sum(stats["s2_coverages"]) / len(stats["s2_coverages"])
                          if stats["s2_coverages"] else None)
            else:
                avg_glance = None
                avg_s9b = None
                n_tests = 0
                avg_s2 = None

            gas.append({
                "ga_image_id": gid,
                "title": img.get("title") or img["filename"],
                "filename": img["filename"],
                "domain": d,
                "avg_glance": round(avg_glance, 4) if avg_glance is not None else None,
                "avg_s9b": round(avg_s9b, 4) if avg_s9b is not None else None,
                "n_tests": n_tests,
                "avg_s2_coverage": round(avg_s2, 4) if avg_s2 is not None else None,
            })

        # Sort: GAs with data first (by avg_glance desc), then GAs without data
        gas_with_data = sorted(
            [g for g in gas if g["avg_glance"] is not None],
            key=lambda g: g["avg_glance"],
            reverse=True,
        )
        gas_no_data = [g for g in gas if g["avg_glance"] is None]
        sorted_gas = gas_with_data + gas_no_data

        all_scores = [g["avg_glance"] for g in gas_with_data]
        total_tests = sum(g["n_tests"] for g in gas)

        result[domain_key] = {
            "label": label,
            "gas": sorted_gas,
            "n_gas": len(gas),
            "n_tests": total_tests,
            "top_score": max(all_scores) if all_scores else None,
            "avg_score": (sum(all_scores) / len(all_scores)) if all_scores else None,
        }

    return result


def get_ga_detail_stats(ga_image_id: int) -> dict:
    """Compute detailed aggregate stats for a single GA image.

    Queries all tests for this GA and computes:
    - avg/individual S9a, S9b, S9c, composite, fluency scores
    - S2 node coverage aggregates
    - speed-accuracy distribution
    - test count and timing

    Returns dict with all computed aggregates, safe for 0-test case.
    """
    from db import get_tests_for_image
    import json

    tests = get_tests_for_image(ga_image_id)
    n = len(tests)

    if n == 0:
        return {
            "n_tests": 0,
            "avg_s9a": 0.0,
            "avg_s9b": 0.0,
            "avg_s9c": 0.0,
            "avg_glance": 0.0,
            "avg_fluency": 0.0,
            "avg_s2_coverage": 0.0,
            "s2_node_aggregates": {},
            "speed_dist": {"fast_right": 0, "slow_right": 0, "fast_wrong": 0, "slow_wrong": 0},
            "tests": [],
        }

    # S9a: use s9a_score (continuous) if available, else binary pass
    s9a_scores = [float(t.get("s9a_score") or 0.0) for t in tests]
    avg_s9a = sum(s9a_scores) / n

    # S9b: binary pass rate
    s9b_passes = [1 if t.get("s9b_pass") else 0 for t in tests]
    avg_s9b = sum(s9b_passes) / n

    # S9c: graduated score
    s9c_scores = [float(t.get("s9c_score") or 0.0) for t in tests]
    avg_s9c = sum(s9c_scores) / n

    # GLANCE composite
    glance_scores = [float(t.get("glance_score") or 0.0) for t in tests]
    avg_glance = sum(glance_scores) / n

    # Fluency
    fluency_scores = [
        compute_fluency_score(bool(t.get("s9b_pass")), t.get("q2_time_ms", 0))
        for t in tests
    ]
    avg_fluency = sum(fluency_scores) / n

    # Normalize fluency to 0-1 range for radar chart (max theoretical ~ 0.22 at 100ms)
    # Use 0.15 as practical max for normalization
    fluency_normalized = min(1.0, avg_fluency / 0.15) if avg_fluency > 0 else 0.0

    # Speed-accuracy distribution
    speed_dist = compute_speed_accuracy_distribution(tests)

    # S2 node coverage aggregates
    s2_coverages = []
    s2_node_aggregates = {}  # node_id -> list of scores across tests
    for t in tests:
        if t.get("s2_node_coverage"):
            try:
                cov = json.loads(t["s2_node_coverage"])
                from scoring import compute_system2_coverage
                s2_coverages.append(compute_system2_coverage(cov))
                for node_id, score in cov.items():
                    s2_node_aggregates.setdefault(node_id, []).append(score)
            except (json.JSONDecodeError, Exception):
                pass

    avg_s2_coverage = (sum(s2_coverages) / len(s2_coverages)) if s2_coverages else 0.0

    # Average per-node scores
    s2_node_means = {
        nid: sum(scores) / len(scores)
        for nid, scores in s2_node_aggregates.items()
    }

    return {
        "n_tests": n,
        "avg_s9a": round(avg_s9a, 4),
        "avg_s9b": round(avg_s9b, 4),
        "avg_s9c": round(avg_s9c, 4),
        "avg_glance": round(avg_glance, 4),
        "avg_fluency": round(avg_fluency, 4),
        "fluency_normalized": round(fluency_normalized, 4),
        "avg_s2_coverage": round(avg_s2_coverage, 4),
        "s2_node_means": s2_node_means,
        "speed_dist": speed_dist,
        "tests": tests,
    }


def get_domain_leaderboard(domain: str, domain_config: dict) -> dict | None:
    """Return detailed leaderboard for a single domain.

    Args:
        domain: domain key (e.g. "med", "tech")
        domain_config: dict from config.yaml["domains"]

    Returns:
        dict with:
            label, gas (sorted list), summary stats (avg, median, std, n_gas, n_tests)
        or None if domain has no images.
    """
    from db import get_db
    import json

    db = get_db()

    images = db.execute(
        "SELECT * FROM ga_images WHERE domain = ? ORDER BY id", (domain,)
    ).fetchall()
    images = [dict(r) for r in images]

    if not images:
        db.close()
        return None

    image_ids = [img["id"] for img in images]
    placeholders = ",".join("?" * len(image_ids))
    test_rows = db.execute(
        f"""SELECT ga_image_id,
                   glance_score,
                   s9b_pass,
                   s9a_score,
                   s2_node_coverage
            FROM tests
            WHERE ga_image_id IN ({placeholders})""",
        image_ids,
    ).fetchall()
    db.close()

    # Aggregate per GA
    ga_stats = {}
    for t in test_rows:
        gid = t["ga_image_id"]
        if gid not in ga_stats:
            ga_stats[gid] = {
                "glance_scores": [],
                "s9b_passes": [],
                "s9a_scores": [],
                "s2_coverages": [],
            }
        ga_stats[gid]["glance_scores"].append(t["glance_score"] or 0.0)
        ga_stats[gid]["s9b_passes"].append(1 if t["s9b_pass"] else 0)
        ga_stats[gid]["s9a_scores"].append(t["s9a_score"] or 0.0)
        if t["s2_node_coverage"]:
            try:
                cov = json.loads(t["s2_node_coverage"])
                from scoring import compute_system2_coverage
                ga_stats[gid]["s2_coverages"].append(compute_system2_coverage(cov))
            except Exception:
                pass

    gas = []
    for img in images:
        gid = img["id"]
        stats = ga_stats.get(gid)
        if stats and stats["glance_scores"]:
            avg_glance = sum(stats["glance_scores"]) / len(stats["glance_scores"])
            avg_s9b = sum(stats["s9b_passes"]) / len(stats["s9b_passes"])
            avg_s9a = sum(stats["s9a_scores"]) / len(stats["s9a_scores"])
            n_tests = len(stats["glance_scores"])
            avg_s2 = (sum(stats["s2_coverages"]) / len(stats["s2_coverages"])
                      if stats["s2_coverages"] else None)
        else:
            avg_glance = None
            avg_s9b = None
            avg_s9a = None
            n_tests = 0
            avg_s2 = None

        gas.append({
            "ga_image_id": gid,
            "title": img.get("title") or img["filename"],
            "filename": img["filename"],
            "domain": domain,
            "avg_glance": round(avg_glance, 4) if avg_glance is not None else None,
            "avg_s9b": round(avg_s9b, 4) if avg_s9b is not None else None,
            "avg_s9a": round(avg_s9a, 4) if avg_s9a is not None else None,
            "n_tests": n_tests,
            "avg_s2_coverage": round(avg_s2, 4) if avg_s2 is not None else None,
        })

    # Sort: data first by avg_glance desc, then no-data
    gas_with_data = sorted(
        [g for g in gas if g["avg_glance"] is not None],
        key=lambda g: g["avg_glance"],
        reverse=True,
    )
    gas_no_data = [g for g in gas if g["avg_glance"] is None]
    sorted_gas = gas_with_data + gas_no_data

    all_scores = [g["avg_glance"] for g in gas_with_data]
    total_tests = sum(g["n_tests"] for g in gas)

    # Summary stats
    if all_scores:
        avg_score = sum(all_scores) / len(all_scores)
        median_score = statistics.median(all_scores)
        std_score = statistics.stdev(all_scores) if len(all_scores) > 1 else 0.0
    else:
        avg_score = None
        median_score = None
        std_score = None

    label = domain_config.get(domain, {}).get("label", domain)

    return {
        "domain": domain,
        "label": label,
        "gas": sorted_gas,
        "n_gas": len(gas),
        "n_tests": total_tests,
        "avg_score": round(avg_score, 4) if avg_score is not None else None,
        "median_score": round(median_score, 4) if median_score is not None else None,
        "std_score": round(std_score, 4) if std_score is not None else None,
    }
