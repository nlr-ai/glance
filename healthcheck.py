"""GLANCE Health Check — verify every feature is functional."""

import os
import time
import logging

logger = logging.getLogger("healthcheck")
BASE = os.path.dirname(os.path.abspath(__file__))


def run_health_check():
    """Run all health checks. Returns dict with pass/fail per feature."""
    results = {}

    # 1. DB accessible
    try:
        from db import get_db
        db = get_db()
        count = db.execute("SELECT COUNT(*) FROM ga_images").fetchone()[0]
        db.close()
        results["db"] = {"pass": True, "detail": f"{count} GAs"}
    except Exception as e:
        results["db"] = {"pass": False, "detail": str(e)}

    # 2. Graphs exist
    try:
        from db import get_db
        db = get_db()
        graphs = db.execute("SELECT COUNT(*) FROM ga_graphs").fetchone()[0]
        sims = db.execute("SELECT COUNT(*) FROM reading_simulations").fetchone()[0]
        db.close()
        results["graphs"] = {"pass": graphs > 0, "detail": f"{graphs} graphs, {sims} sims"}
    except Exception as e:
        results["graphs"] = {"pass": False, "detail": str(e)}

    # 3. Vision scorer importable + Gemini key set
    try:
        from vision_scorer import analyze_ga_image
        key = os.environ.get("GEMINI_API_KEY", "")
        results["vision"] = {"pass": bool(key), "detail": f"key={'set' if key else 'MISSING'}"}
    except Exception as e:
        results["vision"] = {"pass": False, "detail": str(e)}

    # 4. Channel analyzer importable
    try:
        from channel_analyzer import analyze_ga_channels
        results["channels"] = {"pass": True, "detail": "importable"}
    except Exception as e:
        results["channels"] = {"pass": False, "detail": str(e)}

    # 5. Reader sim functional
    try:
        from reader_sim import simulate_reading
        test_graph = {"nodes": [
            {"id": "thing:a", "name": "A", "node_type": "thing", "weight": 0.8},
            {"id": "thing:b", "name": "B", "node_type": "thing", "weight": 0.5},
        ], "links": [], "metadata": {}}
        sim = simulate_reading(test_graph, total_ticks=10)
        results["reader_sim"] = {"pass": "stats" in sim, "detail": f"verdict={sim['stats']['complexity_verdict']}"}
    except Exception as e:
        results["reader_sim"] = {"pass": False, "detail": str(e)}

    # 6. Graph renderer importable
    try:
        from graph_renderer import render_overlay_svg
        results["renderer"] = {"pass": True, "detail": "importable"}
    except Exception as e:
        results["renderer"] = {"pass": False, "detail": str(e)}

    # 7. Deepen importable
    try:
        from deepen import deepen
        results["deepen"] = {"pass": True, "detail": "importable"}
    except Exception as e:
        results["deepen"] = {"pass": False, "detail": str(e)}

    # 8. Claim extractor importable
    try:
        from claim_extractor import extract_claims
        results["claims"] = {"pass": True, "detail": "importable"}
    except Exception as e:
        results["claims"] = {"pass": False, "detail": str(e)}

    # 9. Templates exist
    templates_needed = [
        "index.html", "analyze.html", "ga_detail.html", "leaderboard.html",
        "blog.html", "profile.html", "auth_login.html", "changelog.html",
    ]
    missing = [t for t in templates_needed if not os.path.exists(os.path.join(BASE, "templates", t))]
    results["templates"] = {"pass": len(missing) == 0, "detail": f"{len(templates_needed) - len(missing)}/{len(templates_needed)}" + (f" missing: {missing}" if missing else "")}

    # 10. GA library accessible
    lib_path = os.path.join(BASE, "ga_library")
    if os.path.exists(lib_path):
        n_files = len([f for f in os.listdir(lib_path) if f.endswith((".png", ".jpg", ".jpeg"))])
        results["ga_library"] = {"pass": n_files > 0, "detail": f"{n_files} images"}
    else:
        results["ga_library"] = {"pass": False, "detail": "directory missing"}

    # Summary
    total = len(results)
    passed = sum(1 for r in results.values() if r["pass"])
    results["_summary"] = {"total": total, "passed": passed, "failed": total - passed}

    return results
