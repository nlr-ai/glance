"""GLANCE analytics — aggregate statistics per S2b_Mathematics.md.

All formulas from sections 2-7 of the mathematical model.
"""

import math
import os
import json
import statistics
from datetime import datetime, timedelta

from scoring import classify_speed_accuracy, classify_rt2, score_glance_composite
from config_loader import get_constant

# Base directory for sidecar JSON lookups
_ANALYTICS_BASE = os.path.dirname(os.path.abspath(__file__))


def _get_predicted_score(filename):
    """Try to get predicted score from sidecar JSON.

    Priority: predicted_score > approximated_scores.s9b
    Returns (score_0_to_1, source_label) or (None, None).
    """
    if not filename:
        return None, None
    slug = os.path.splitext(filename)[0]
    sidecar_path = os.path.join(_ANALYTICS_BASE, "ga_library", f"{slug}.json")
    if not os.path.exists(sidecar_path):
        return None, None
    try:
        with open(sidecar_path, encoding="utf-8") as f:
            data = json.load(f)
        # Priority: predicted_score > approximated_scores.s9b
        ps = data.get("predicted_score")
        if ps is not None:
            return ps / 100 if ps > 1 else ps, "predicted"
        approx = data.get("approximated_scores", {})
        s9b = approx.get("s9b")
        if s9b is not None:
            return s9b, "approximated"
    except Exception:
        pass
    return None, None

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


# ── KPI Evolution (week-over-week delta) ─────────────────────────────


def compute_kpi_evolution(tests: list[dict]) -> dict:
    """Compute week-over-week evolution for dashboard KPI cards.

    Splits tests into current period (last 7 days) and previous period
    (7-14 days ago) based on created_at timestamps. For each KPI, computes:
        - current: value for last 7 days
        - previous: value for 7-14 days ago
        - delta_pct: ((current - previous) / previous) * 100
        - arrow: "up" | "down" | "flat"
        - label: formatted string e.g. "+23%" or "-12%" or "0%"

    If no previous period data exists (first week), delta fields are None.

    Returns:
        {
            "tests_completed": { current, previous, delta_pct, arrow, label },
            "unique_participants": { current, previous, delta_pct, arrow, label },
            "avg_glance": { current, previous, delta_pct, arrow, label },
            "completion_rate": { current, previous, delta_pct, arrow, label },
        }
    """
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    def parse_ts(t):
        """Parse created_at string to datetime. Handles common SQLite formats."""
        ts = t.get("created_at", "")
        if not ts:
            return None
        try:
            # SQLite datetime('now') format: "2026-03-25 14:30:00"
            return datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            try:
                return datetime.strptime(ts[:10], "%Y-%m-%d")
            except (ValueError, TypeError):
                return None

    current_tests = []
    previous_tests = []
    for t in tests:
        dt = parse_ts(t)
        if dt is None:
            continue
        if dt >= seven_days_ago:
            current_tests.append(t)
        elif dt >= fourteen_days_ago:
            previous_tests.append(t)

    def _make_delta(current_val, previous_val):
        """Build a delta dict from two numeric values."""
        if previous_val is None or len(previous_tests) == 0:
            return {
                "current": current_val,
                "previous": None,
                "delta_pct": None,
                "arrow": None,
                "label": None,
            }
        if previous_val == 0:
            if current_val == 0:
                pct = 0.0
            else:
                pct = 100.0  # went from 0 to something
        else:
            pct = ((current_val - previous_val) / previous_val) * 100.0

        pct = round(pct, 1)
        if pct > 0:
            arrow = "up"
            label = f"+{pct}%"
        elif pct < 0:
            arrow = "down"
            label = f"{pct}%"
        else:
            arrow = "flat"
            label = "0%"

        return {
            "current": current_val,
            "previous": previous_val,
            "delta_pct": pct,
            "arrow": arrow,
            "label": label,
        }

    # KPI 1: Tests completed
    n_current = len(current_tests)
    n_previous = len(previous_tests)

    # KPI 2: Unique participants
    current_participants = len(set(t.get("participant_id") for t in current_tests if t.get("participant_id")))
    previous_participants = len(set(t.get("participant_id") for t in previous_tests if t.get("participant_id")))

    # KPI 3: Average GLANCE score
    current_glance_scores = [float(t.get("glance_score") or 0.0) for t in current_tests]
    previous_glance_scores = [float(t.get("glance_score") or 0.0) for t in previous_tests]
    avg_glance_current = (sum(current_glance_scores) / len(current_glance_scores)) if current_glance_scores else 0.0
    avg_glance_previous = (sum(previous_glance_scores) / len(previous_glance_scores)) if previous_glance_scores else 0.0

    # KPI 4: Completion rate (tests with glance_score > 0 / total tests)
    # Proxy: a completed test has all three S9 sub-scores filled
    def _completion_rate(test_list):
        if not test_list:
            return 0.0
        completed = sum(
            1 for t in test_list
            if t.get("s9a_pass") is not None
            and t.get("s9b_pass") is not None
            and t.get("s9c_pass") is not None
        )
        return completed / len(test_list)

    completion_current = _completion_rate(current_tests)
    completion_previous = _completion_rate(previous_tests)

    return {
        "tests_completed": _make_delta(n_current, n_previous),
        "unique_participants": _make_delta(current_participants, previous_participants),
        "avg_glance": _make_delta(round(avg_glance_current, 4), round(avg_glance_previous, 4)),
        "completion_rate": _make_delta(round(completion_current, 4), round(completion_previous, 4)),
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
    images = db.execute("SELECT * FROM ga_images WHERE public = 1 ORDER BY id").fetchall()
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

            # Predicted score fallback when no real tests
            score_source = "measured" if avg_glance is not None else None
            display_score = avg_glance
            if avg_glance is None:
                pred_score, pred_source = _get_predicted_score(img["filename"])
                if pred_score is not None:
                    display_score = pred_score
                    score_source = pred_source

            gas.append({
                "ga_image_id": gid,
                "slug": img.get("slug") or str(gid),
                "title": img.get("title") or img["filename"],
                "filename": img["filename"],
                "domain": d,
                "avg_glance": round(avg_glance, 4) if avg_glance is not None else None,
                "display_score": round(display_score, 4) if display_score is not None else None,
                "score_source": score_source,
                "avg_s9b": round(avg_s9b, 4) if avg_s9b is not None else None,
                "n_tests": n_tests,
                "avg_s2_coverage": round(avg_s2, 4) if avg_s2 is not None else None,
            })

        # Sort: GAs with real data first (by avg_glance desc),
        # then predicted scores, then no data at all
        gas_with_data = sorted(
            [g for g in gas if g["avg_glance"] is not None],
            key=lambda g: g["avg_glance"],
            reverse=True,
        )
        gas_predicted = sorted(
            [g for g in gas if g["avg_glance"] is None and g["display_score"] is not None],
            key=lambda g: g["display_score"],
            reverse=True,
        )
        gas_no_data = [g for g in gas if g["avg_glance"] is None and g["display_score"] is None]
        sorted_gas = gas_with_data + gas_predicted + gas_no_data

        all_scores = [g["avg_glance"] for g in gas_with_data]
        total_tests = sum(g["n_tests"] for g in gas)

        # Compute avg_display_score: uses real scores if available,
        # otherwise falls back to predicted/display scores for gallery view
        all_display = [g["display_score"] for g in sorted_gas if g["display_score"] is not None]
        avg_display = (sum(all_display) / len(all_display)) if all_display else None

        dcfg = domain_config.get(domain_key, {})
        result[domain_key] = {
            "label": label,
            "emoji": dcfg.get("emoji", ""),
            "color": dcfg.get("color", "#71717a"),
            "gas": sorted_gas,
            "n_gas": len(gas),
            "n_tests": total_tests,
            "top_score": max(all_scores) if all_scores else None,
            "avg_score": (sum(all_scores) / len(all_scores)) if all_scores else None,
            "avg_display_score": round(avg_display, 4) if avg_display is not None else None,
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

        # Predicted score fallback when no real tests
        score_source = "measured" if avg_glance is not None else None
        display_score = avg_glance
        if avg_glance is None:
            pred_score, pred_source = _get_predicted_score(img["filename"])
            if pred_score is not None:
                display_score = pred_score
                score_source = pred_source

        gas.append({
            "ga_image_id": gid,
            "slug": img.get("slug") or str(gid),
            "title": img.get("title") or img["filename"],
            "filename": img["filename"],
            "domain": domain,
            "avg_glance": round(avg_glance, 4) if avg_glance is not None else None,
            "display_score": round(display_score, 4) if display_score is not None else None,
            "score_source": score_source,
            "avg_s9b": round(avg_s9b, 4) if avg_s9b is not None else None,
            "avg_s9a": round(avg_s9a, 4) if avg_s9a is not None else None,
            "n_tests": n_tests,
            "avg_s2_coverage": round(avg_s2, 4) if avg_s2 is not None else None,
        })

    # Sort: real data first (by avg_glance desc), then predicted, then no data
    gas_with_data = sorted(
        [g for g in gas if g["avg_glance"] is not None],
        key=lambda g: g["avg_glance"],
        reverse=True,
    )
    gas_predicted = sorted(
        [g for g in gas if g["avg_glance"] is None and g["display_score"] is not None],
        key=lambda g: g["display_score"],
        reverse=True,
    )
    gas_no_data = [g for g in gas if g["avg_glance"] is None and g["display_score"] is None]
    sorted_gas = gas_with_data + gas_predicted + gas_no_data

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

    # avg_display_score: fallback using predicted scores when no real tests
    all_display = [g["display_score"] for g in sorted_gas if g["display_score"] is not None]
    avg_display = (sum(all_display) / len(all_display)) if all_display else None

    dcfg = domain_config.get(domain, {})
    label = dcfg.get("label", domain)

    return {
        "domain": domain,
        "label": label,
        "emoji": dcfg.get("emoji", ""),
        "color": dcfg.get("color", "#71717a"),
        "gas": sorted_gas,
        "n_gas": len(gas),
        "n_tests": total_tests,
        "avg_score": round(avg_score, 4) if avg_score is not None else None,
        "avg_display_score": round(avg_display, 4) if avg_display is not None else None,
        "median_score": round(median_score, 4) if median_score is not None else None,
        "std_score": round(std_score, 4) if std_score is not None else None,
    }


# ── Score Distribution analytics ─────────────────────────────────────


def get_score_distributions() -> dict:
    """Return score distributions across ALL GAs for distribution charts.

    Computes per-GA average scores for s9a, s9b, s9c, and glance_score,
    then returns sorted lists for each metric. Used to render inline SVG
    histograms on the GA detail page.

    Returns:
        {
            "s9a": [float, ...],       # sorted avg S9a scores per GA
            "s9b": [float, ...],       # sorted avg S9b scores per GA
            "s9c": [float, ...],       # sorted avg S9c scores per GA
            "glance": [float, ...],    # sorted avg GLANCE scores per GA
            "n_gas": int,              # total GAs with test data
        }
    """
    from db import get_db
    import json

    db = get_db()

    # Get all tests grouped by GA
    test_rows = db.execute(
        """SELECT ga_image_id,
                  s9a_score,
                  s9b_pass,
                  s9c_score,
                  glance_score
           FROM tests
           WHERE ga_image_id IS NOT NULL"""
    ).fetchall()
    db.close()

    # Build per-GA aggregates
    ga_data = {}  # ga_image_id -> {s9a: [], s9b: [], s9c: [], glance: []}
    for t in test_rows:
        gid = t["ga_image_id"]
        if gid not in ga_data:
            ga_data[gid] = {"s9a": [], "s9b": [], "s9c": [], "glance": []}
        ga_data[gid]["s9a"].append(float(t["s9a_score"] or 0.0))
        ga_data[gid]["s9b"].append(1.0 if t["s9b_pass"] else 0.0)
        ga_data[gid]["s9c"].append(float(t["s9c_score"] or 0.0))
        ga_data[gid]["glance"].append(float(t["glance_score"] or 0.0))

    # Compute per-GA averages
    distributions = {"s9a": [], "s9b": [], "s9c": [], "glance": []}
    for gid, data in ga_data.items():
        n = len(data["glance"])
        if n > 0:
            distributions["s9a"].append(sum(data["s9a"]) / n)
            distributions["s9b"].append(sum(data["s9b"]) / n)
            distributions["s9c"].append(sum(data["s9c"]) / n)
            distributions["glance"].append(sum(data["glance"]) / n)

    # Sort each
    for key in distributions:
        distributions[key].sort()

    distributions["n_gas"] = len(distributions["glance"])
    return distributions


def get_admin_analytics() -> dict:
    """Return comprehensive platform analytics for admin dashboard.

    Queries all participants, tests, and images to compute:
    - Overview KPIs (total visitors, tests completed, averages, completion rate)
    - Tests per day (last 30 days)
    - Score distribution (histogram bins)
    - Domain performance (avg S9b, GLANCE per domain)
    - VEC vs Control comparison per domain
    - Profile distributions (clinical_domain, data_literacy, experience_years)
    - Input mode comparison (voice vs text S9a)
    - All test rows for the response table

    Returns a dict with all computed analytics, safe for empty DB.
    """
    from db import get_db
    from datetime import datetime, timedelta

    db = get_db()

    # ── Participants ──
    participants = [dict(r) for r in db.execute("SELECT * FROM participants ORDER BY created_at").fetchall()]
    n_participants = len(participants)

    # ── All tests with joins ──
    all_tests_rows = db.execute(
        """SELECT t.id, t.created_at, t.participant_id, t.ga_image_id,
                  t.q1_text, t.q1_time_ms, t.q2_choice, t.q2_time_ms,
                  t.q3_choice, t.q3_time_ms,
                  t.s9a_pass, t.s9a_score, t.s9b_pass, t.s9c_pass,
                  t.s9c_score, t.glance_score, t.speed_accuracy,
                  t.exposure_mode, t.q1_input_mode, t.q1_raw_transcript,
                  t.exposure_actual_ms,
                  p.clinical_domain, p.data_literacy, p.experience_years,
                  p.input_mode as participant_input_mode,
                  g.title as ga_title, g.domain, g.is_control, g.filename
           FROM tests t
           JOIN participants p ON t.participant_id = p.id
           JOIN ga_images g ON t.ga_image_id = g.id
           ORDER BY t.created_at DESC"""
    ).fetchall()
    db.close()

    all_tests = [dict(r) for r in all_tests_rows]
    n_tests = len(all_tests)

    # ── Overview KPIs ──
    today = datetime.utcnow().strftime("%Y-%m-%d")
    week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    tests_today = sum(1 for t in all_tests if t["created_at"] and t["created_at"][:10] == today)
    tests_this_week = sum(1 for t in all_tests if t["created_at"] and t["created_at"][:10] >= week_ago)

    glance_scores = [float(t.get("glance_score") or 0.0) for t in all_tests]
    avg_glance = (sum(glance_scores) / len(glance_scores)) if glance_scores else 0.0

    # Average session duration estimate: sum of q1_time + q2_time + q3_time per test
    session_durations = []
    for t in all_tests:
        dur = (t.get("q1_time_ms") or 0) + (t.get("q2_time_ms") or 0) + (t.get("q3_time_ms") or 0)
        if t.get("exposure_actual_ms"):
            dur += t["exposure_actual_ms"]
        if dur > 0:
            session_durations.append(dur)
    avg_session_ms = (sum(session_durations) / len(session_durations)) if session_durations else 0

    # Completion rate: participants who completed at least 1 test / total participants
    participants_with_tests = len(set(t["participant_id"] for t in all_tests))
    completion_rate = (participants_with_tests / n_participants * 100) if n_participants > 0 else 0.0

    # ── Tests per day (last 30 days) ──
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    day_counts = {}
    for t in all_tests:
        day = t["created_at"][:10] if t["created_at"] else None
        if day and day >= thirty_days_ago:
            day_counts[day] = day_counts.get(day, 0) + 1

    # Fill in missing days with 0
    tests_per_day = []
    base_date = datetime.utcnow() - timedelta(days=29)
    for i in range(30):
        d = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        tests_per_day.append({"date": d, "count": day_counts.get(d, 0)})

    # ── Score distribution (10 bins from 0-100%) ──
    score_bins = [0] * 10
    for s in glance_scores:
        pct = s * 100
        bin_idx = min(int(pct // 10), 9)  # 0-9
        score_bins[bin_idx] += 1

    # ── Domain scores ──
    domain_data = {}  # domain -> {s9b_passes, glance_scores, n}
    for t in all_tests:
        d = t.get("domain", "unknown")
        if d not in domain_data:
            domain_data[d] = {"s9b_passes": 0, "n": 0, "glance_sum": 0.0}
        domain_data[d]["n"] += 1
        if t.get("s9b_pass"):
            domain_data[d]["s9b_passes"] += 1
        domain_data[d]["glance_sum"] += float(t.get("glance_score") or 0.0)

    domain_scores = []
    for d, dd in sorted(domain_data.items()):
        domain_scores.append({
            "domain": d,
            "avg_s9b": round(dd["s9b_passes"] / dd["n"], 4) if dd["n"] > 0 else 0,
            "avg_glance": round(dd["glance_sum"] / dd["n"], 4) if dd["n"] > 0 else 0,
            "n_tests": dd["n"],
        })

    # ── VEC vs Control per domain ──
    vec_ctrl_data = {}  # domain -> {vec_s9b_passes, vec_n, ctrl_s9b_passes, ctrl_n}
    for t in all_tests:
        d = t.get("domain", "unknown")
        if d not in vec_ctrl_data:
            vec_ctrl_data[d] = {"vec_s9b": 0, "vec_n": 0, "ctrl_s9b": 0, "ctrl_n": 0}
        if t.get("is_control"):
            vec_ctrl_data[d]["ctrl_n"] += 1
            if t.get("s9b_pass"):
                vec_ctrl_data[d]["ctrl_s9b"] += 1
        else:
            vec_ctrl_data[d]["vec_n"] += 1
            if t.get("s9b_pass"):
                vec_ctrl_data[d]["vec_s9b"] += 1

    vec_vs_control = []
    for d, dd in sorted(vec_ctrl_data.items()):
        if dd["vec_n"] > 0 or dd["ctrl_n"] > 0:
            vec_vs_control.append({
                "domain": d,
                "vec_s9b": round(dd["vec_s9b"] / dd["vec_n"], 4) if dd["vec_n"] > 0 else 0,
                "control_s9b": round(dd["ctrl_s9b"] / dd["ctrl_n"], 4) if dd["ctrl_n"] > 0 else 0,
                "vec_n": dd["vec_n"],
                "control_n": dd["ctrl_n"],
            })

    # ── Profile distributions ──
    clinical_dist = {}
    literacy_dist = {}
    experience_dist = {}
    for p in participants:
        cd = p.get("clinical_domain", "unknown") or "unknown"
        dl = p.get("data_literacy", "unknown") or "unknown"
        ey = p.get("experience_years", "unknown") or "unknown"
        clinical_dist[cd] = clinical_dist.get(cd, 0) + 1
        literacy_dist[dl] = literacy_dist.get(dl, 0) + 1
        experience_dist[ey] = experience_dist.get(ey, 0) + 1

    # ── Input mode comparison (voice vs text S9a) ──
    voice_s9a = []
    text_s9a = []
    for t in all_tests:
        mode = t.get("q1_input_mode", "text") or "text"
        s9a = float(t.get("s9a_score") or 0.0)
        if mode == "voice":
            voice_s9a.append(s9a)
        else:
            text_s9a.append(s9a)

    input_mode_comparison = {
        "voice": {
            "avg_s9a": round(sum(voice_s9a) / len(voice_s9a), 4) if voice_s9a else 0,
            "n": len(voice_s9a),
        },
        "text": {
            "avg_s9a": round(sum(text_s9a) / len(text_s9a), 4) if text_s9a else 0,
            "n": len(text_s9a),
        },
    }

    # ── All tests for response table ──
    response_table = []
    for t in all_tests:
        response_table.append({
            "date": t["created_at"][:16] if t["created_at"] else "",
            "profile": f"{t.get('clinical_domain', '-')} / {t.get('data_literacy', '-')}",
            "ga_title": t.get("ga_title") or "-",
            "domain": t.get("domain", "-"),
            "mode": t.get("exposure_mode", "spotlight"),
            "input_mode": t.get("q1_input_mode", "text"),
            "s9a": int(t.get("s9a_pass") or 0),
            "s9a_score": round(float(t.get("s9a_score") or 0), 3),
            "s9b": int(t.get("s9b_pass") or 0),
            "s9c": int(t.get("s9c_pass") or 0),
            "glance": round(float(t.get("glance_score") or 0) * 100, 1),
            "rt2": round((t.get("q2_time_ms") or 0) / 1000, 1),
            "speed_accuracy": t.get("speed_accuracy") or "-",
            "q1_text": (t.get("q1_text") or "")[:80],
            "q2_choice": t.get("q2_choice") or "-",
        })

    # ── Graphs ──
    db2 = get_db()
    graphs_rows = db2.execute("""
        SELECT g.id, g.ga_image_id, g.graph_type, g.created_at, g.source, g.version,
               g.node_count, g.link_count, g.avg_effectiveness, g.anti_pattern_count,
               i.filename as ga_filename, i.slug as ga_slug
        FROM ga_graphs g
        LEFT JOIN ga_images i ON g.ga_image_id = i.id
        ORDER BY g.id DESC
    """).fetchall()
    graphs = [dict(r) for r in graphs_rows]

    # ── Reading simulations ──
    sims_rows = db2.execute("""
        SELECT rs.id, rs.ga_image_id, rs.graph_id, rs.created_at, rs.mode,
               rs.total_ticks, rs.ticks_used, rs.budget_pressure, rs.complexity_verdict,
               rs.nodes_visited, rs.nodes_total, rs.nodes_skipped,
               rs.narrative_coverage, rs.avg_narrative_attention,
               rs.dead_space_count, rs.orphan_narrative_count,
               rs.narrative_text,
               i.filename as ga_filename, i.slug as ga_slug
        FROM reading_simulations rs
        LEFT JOIN ga_images i ON rs.ga_image_id = i.id
        ORDER BY rs.id DESC
    """).fetchall()
    sims = [dict(r) for r in sims_rows]
    db2.close()

    return {
        "kpis": {
            "n_participants": n_participants,
            "n_tests": n_tests,
            "tests_today": tests_today,
            "tests_this_week": tests_this_week,
            "avg_glance": round(avg_glance * 100, 1),
            "avg_session_s": round(avg_session_ms / 1000, 1) if avg_session_ms > 0 else 0,
            "completion_rate": round(completion_rate, 1),
        },
        "tests_per_day": tests_per_day,
        "score_distribution": score_bins,
        "domain_scores": domain_scores,
        "vec_vs_control": vec_vs_control,
        "profile_distribution": {
            "clinical_domain": clinical_dist,
            "data_literacy": literacy_dist,
            "experience_years": experience_dist,
        },
        "input_mode_comparison": input_mode_comparison,
        "response_table": response_table,
        "graphs": graphs,
        "reading_sims": sims,
    }


def get_domain_rank(ga_image_id: int, domain: str) -> dict:
    """Compute rank and percentile of a GA within its domain.

    Queries all GAs in the same domain, computes their average GLANCE scores,
    and finds where this GA sits.

    Returns:
        {
            "rank": int,              # 1-indexed rank (1 = best)
            "total_in_domain": int,   # total GAs with data in domain
            "percentile": float,      # percentage of GAs this one beats (0-100)
            "domain_label": str,      # human-readable domain label
        }
    """
    from db import get_db

    db = get_db()

    # All GA images in this domain
    images = db.execute(
        "SELECT id FROM ga_images WHERE domain = ?", (domain,)
    ).fetchall()
    image_ids = [r["id"] for r in images]

    if not image_ids:
        db.close()
        return {"rank": 0, "total_in_domain": 0, "percentile": 0.0, "domain_label": domain}

    # Get average GLANCE per GA in this domain
    placeholders = ",".join("?" * len(image_ids))
    rows = db.execute(
        f"""SELECT ga_image_id, AVG(glance_score) as avg_glance
            FROM tests
            WHERE ga_image_id IN ({placeholders})
            GROUP BY ga_image_id
            HAVING COUNT(*) > 0""",
        image_ids,
    ).fetchall()
    db.close()

    if not rows:
        return {"rank": 0, "total_in_domain": 0, "percentile": 0.0, "domain_label": domain}

    # Sort by avg_glance descending
    scored = [(r["ga_image_id"], r["avg_glance"] or 0.0) for r in rows]
    scored.sort(key=lambda x: x[1], reverse=True)

    total = len(scored)
    rank = 0
    for i, (gid, score) in enumerate(scored):
        if gid == ga_image_id:
            rank = i + 1
            break

    if rank == 0:
        # This GA has no test data
        return {"rank": 0, "total_in_domain": total, "percentile": 0.0, "domain_label": domain}

    # Percentile: percentage of GAs this one beats
    # rank 1 out of 10 -> beats 9/10 = 90%
    # rank 10 out of 10 -> beats 0/10 = 0%
    if total <= 1:
        percentile = 100.0
    else:
        percentile = ((total - rank) / (total - 1)) * 100.0

    return {
        "rank": rank,
        "total_in_domain": total,
        "percentile": round(percentile, 0),
        "domain_label": domain,
    }


def get_participant_percentile(participant_id: int) -> int:
    """Compute the percentile rank of a participant among all participants.

    Percentile = percentage of participants whose average GLANCE score is
    lower than this participant's average GLANCE score.

    Returns:
        int: percentile (0-100). 95 means "better than 95% of testers".
             Returns 0 if the participant has no test data or there are
             fewer than 2 participants with data.
    """
    from db import get_db

    db = get_db()

    # Get average GLANCE score per participant (only participants with tests)
    rows = db.execute(
        """SELECT participant_id, AVG(glance_score) as avg_glance
           FROM tests
           GROUP BY participant_id
           HAVING COUNT(*) > 0"""
    ).fetchall()
    db.close()

    if not rows:
        return 0

    scores_by_pid = {r["participant_id"]: r["avg_glance"] or 0.0 for r in rows}

    if participant_id not in scores_by_pid:
        return 0

    my_score = scores_by_pid[participant_id]
    total = len(scores_by_pid)

    if total <= 1:
        return 100

    # Count how many participants have a strictly lower average score
    n_below = sum(1 for s in scores_by_pid.values() if s < my_score)
    percentile = (n_below / (total - 1)) * 100.0

    return round(percentile)


# ── Participant Rankings ────────────────────────────────────────────


def get_participant_ranking_comprehension(min_tests: int = 3) -> list[dict]:
    """Rank participants by average GLANCE composite score (comprehension).

    Only includes participants with at least `min_tests` completed tests,
    to avoid single-test flukes inflating the ranking.

    For each qualifying participant, computes:
    - avg_glance: average GLANCE composite score across all their tests
    - n_tests: total tests completed
    - best_score: highest single-test GLANCE score
    - streak: consecutive tests (ordered by created_at) with score >= 0.70
    - profile: anonymized descriptor from clinical_domain + data_literacy
    - percentile: "Top X%" among all qualifying participants

    Returns:
        List of dicts sorted by avg_glance descending.
    """
    from db import get_db

    db = get_db()

    # Get all tests with participant profile data, ordered by participant + time
    rows = db.execute(
        """SELECT t.participant_id, t.glance_score, t.created_at,
                  t.q1_time_ms, t.q2_time_ms, t.q3_time_ms,
                  t.exposure_actual_ms,
                  p.clinical_domain, p.data_literacy, p.experience_years,
                  p.token,
                  g.domain as ga_domain
           FROM tests t
           JOIN participants p ON t.participant_id = p.id
           JOIN ga_images g ON t.ga_image_id = g.id
           ORDER BY t.participant_id, t.created_at ASC"""
    ).fetchall()
    db.close()

    if not rows:
        return []

    # Group by participant
    participants = {}
    for r in rows:
        pid = r["participant_id"]
        if pid not in participants:
            participants[pid] = {
                "participant_id": pid,
                "clinical_domain": r["clinical_domain"],
                "data_literacy": r["data_literacy"],
                "experience_years": r["experience_years"],
                "token": r["token"],
                "scores": [],
                "domains": set(),
                "total_time_ms": 0,
            }
        score = float(r["glance_score"] or 0.0)
        participants[pid]["scores"].append(score)
        participants[pid]["domains"].add(r["ga_domain"])
        # Accumulate response time
        rt = (r["q1_time_ms"] or 0) + (r["q2_time_ms"] or 0) + (r["q3_time_ms"] or 0)
        if r["exposure_actual_ms"]:
            rt += r["exposure_actual_ms"]
        participants[pid]["total_time_ms"] += rt

    # Filter by min_tests and compute metrics
    glance_threshold = get_constant("glance_pass_threshold", 0.70)
    qualifying = []
    for pid, p in participants.items():
        n = len(p["scores"])
        if n < min_tests:
            continue
        qualifying.append((pid, p, n))

    # Bulk-generate handles for qualifying participants
    from handles import get_handle_map
    handle_map = get_handle_map([pid for pid, _, _ in qualifying])

    result = []
    for pid, p, n in qualifying:
        avg_glance = sum(p["scores"]) / n
        best_score = max(p["scores"])

        # Compute current streak: consecutive scores >= threshold from the end
        streak = 0
        for s in reversed(p["scores"]):
            if s >= glance_threshold:
                streak += 1
            else:
                break

        # Build anonymized profile descriptor
        profile = _build_profile_descriptor(
            p["clinical_domain"], p["data_literacy"], p["experience_years"]
        )

        result.append({
            "participant_id": pid,
            "handle": handle_map.get(pid, "Anonymous"),
            "profile": profile,
            "avg_glance": round(avg_glance, 4),
            "n_tests": n,
            "best_score": round(best_score, 4),
            "streak": streak,
            "domains_covered": len(p["domains"]),
            "total_time_s": round(p["total_time_ms"] / 1000, 1),
        })

    # Sort by avg_glance descending
    result.sort(key=lambda x: x["avg_glance"], reverse=True)

    # Compute percentile for each participant
    total = len(result)
    for i, entry in enumerate(result):
        if total <= 1:
            entry["top_pct"] = 1
        else:
            entry["top_pct"] = max(1, round((i / total) * 100))

    return result


def get_participant_ranking_contribution() -> list[dict]:
    """Rank participants by number of tests completed (contribution).

    For each participant, computes:
    - n_tests: total tests completed
    - avg_glance: average GLANCE composite score
    - domains_covered: number of distinct GA domains tested
    - total_time_s: estimated total time from RT sums
    - profile: anonymized descriptor

    Returns:
        List of dicts sorted by n_tests descending.
    """
    from db import get_db

    db = get_db()

    rows = db.execute(
        """SELECT t.participant_id, t.glance_score,
                  t.q1_time_ms, t.q2_time_ms, t.q3_time_ms,
                  t.exposure_actual_ms,
                  p.clinical_domain, p.data_literacy, p.experience_years,
                  p.token,
                  g.domain as ga_domain
           FROM tests t
           JOIN participants p ON t.participant_id = p.id
           JOIN ga_images g ON t.ga_image_id = g.id
           ORDER BY t.participant_id"""
    ).fetchall()
    db.close()

    if not rows:
        return []

    # Group by participant
    participants = {}
    for r in rows:
        pid = r["participant_id"]
        if pid not in participants:
            participants[pid] = {
                "participant_id": pid,
                "clinical_domain": r["clinical_domain"],
                "data_literacy": r["data_literacy"],
                "experience_years": r["experience_years"],
                "token": r["token"],
                "scores": [],
                "domains": set(),
                "total_time_ms": 0,
            }
        participants[pid]["scores"].append(float(r["glance_score"] or 0.0))
        participants[pid]["domains"].add(r["ga_domain"])
        rt = (r["q1_time_ms"] or 0) + (r["q2_time_ms"] or 0) + (r["q3_time_ms"] or 0)
        if r["exposure_actual_ms"]:
            rt += r["exposure_actual_ms"]
        participants[pid]["total_time_ms"] += rt

    # Bulk-generate handles
    from handles import get_handle_map
    handle_map = get_handle_map(list(participants.keys()))

    result = []
    for pid, p in participants.items():
        n = len(p["scores"])
        avg_glance = sum(p["scores"]) / n if n > 0 else 0.0
        profile = _build_profile_descriptor(
            p["clinical_domain"], p["data_literacy"], p["experience_years"]
        )
        result.append({
            "participant_id": pid,
            "handle": handle_map.get(pid, "Anonymous"),
            "profile": profile,
            "n_tests": n,
            "avg_glance": round(avg_glance, 4),
            "domains_covered": len(p["domains"]),
            "total_time_s": round(p["total_time_ms"] / 1000, 1),
        })

    # Sort by n_tests descending, then avg_glance as tiebreaker
    result.sort(key=lambda x: (x["n_tests"], x["avg_glance"]), reverse=True)

    # Compute percentile for each participant
    total = len(result)
    for i, entry in enumerate(result):
        if total <= 1:
            entry["top_pct"] = 1
        else:
            entry["top_pct"] = max(1, round((i / total) * 100))

    return result


def _build_profile_descriptor(clinical_domain: str, data_literacy: str,
                                experience_years: str) -> str:
    """Build an anonymized profile descriptor from participant fields.

    Example output: "Pediatre . 5-15 ans . Profil Tech/Data"
    """
    parts = []

    # Clinical domain — use as-is (already a readable label from onboard form)
    if clinical_domain:
        parts.append(clinical_domain)

    # Experience years
    if experience_years:
        parts.append(experience_years)

    # Data literacy
    if data_literacy:
        parts.append(data_literacy)

    return " · ".join(parts) if parts else "Profil anonyme"
