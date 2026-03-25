"""
GA Auto-Improve — Autonomous iteration loop.

Runs the full GLANCE feedback loop automatically:
  ANALYZE → SCORE → DIAGNOSE → ADVISE → APPLY → RE-SCORE → REPEAT

Each turn:
  1. vision_scorer → L3 graph
  2. channel_analyzer → enriched graph + anti-patterns
  3. archetype classifier → score/tier
  4. ga_advisor → modified graph with fixes
  5. Log the turn: score delta, changes made, anti-patterns resolved

Stops when:
  - max_turns reached (default 5)
  - archetype reaches Cristallin
  - score improvement < 0.02 for 2 consecutive turns (plateau)
  - all anti-patterns resolved

Usage:
    python ga_auto_improve.py <image> [--abstract "..."] [--max-turns 5] [--target-archetype cristallin]

    # With abstract from file
    python ga_auto_improve.py ga.png --abstract-file abstract.txt

    # Aggressive: 10 turns, target Cristallin
    python ga_auto_improve.py ga.png --max-turns 10 --target-archetype cristallin
"""

import os
import sys
import yaml
import json
import time
import logging
import copy

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("auto_improve")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ENV = os.path.join(_HERE, ".env")
if os.path.exists(_ENV):
    with open(_ENV) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)


def _load_abstract(abstract_text=None, abstract_file=None, sidecar_path=None):
    """Load abstract from direct text, file, or sidecar JSON."""
    if abstract_text:
        return abstract_text
    if abstract_file and os.path.exists(abstract_file):
        with open(abstract_file, encoding="utf-8") as f:
            return f.read().strip()
    if sidecar_path and os.path.exists(sidecar_path):
        try:
            with open(sidecar_path) as f:
                data = json.load(f)
            l3 = data.get("semantic_references", {}).get("L3", [])
            if l3:
                return l3[0]
        except Exception:
            pass
    return None


def _build_intent_from_diagnosis(turn_data):
    """Build a targeted improvement intent from the current diagnosis."""
    issues = []

    # Anti-patterns
    for ap in turn_data.get("anti_patterns", []):
        if ap.get("severity") == "HIGH":
            issues.append(ap.get("issue", ""))

    # Low-effectiveness channels
    for ch in turn_data.get("low_channels", []):
        issues.append(f"Channel '{ch['channel']}' has low effectiveness ({ch['effectiveness']:.1f})")

    # Archetype-specific
    archetype = turn_data.get("archetype", "")
    if archetype == "fantome":
        issues.append("The GA communicates NOTHING in 5 seconds — need a clear focal point")
    elif archetype == "encyclopedie":
        issues.append("Too much information, no hierarchy — simplify to 1 main message")
    elif archetype == "desequilibre":
        issues.append("Visual weight is uneven — one element dominates, crushing the rest")
    elif archetype == "embelli":
        issues.append("The hierarchy is communicated but may be biased — verify encoding proportionality")

    # Score-based
    s9b = turn_data.get("s9b", 0)
    if s9b < 0.5:
        issues.append(f"S9b={s9b:.2f} — hierarchy not perceived, need stronger visual dominance of main finding")
    elif s9b < 0.7:
        issues.append(f"S9b={s9b:.2f} — hierarchy partially perceived, strengthen primary bar/element")

    word_count = turn_data.get("word_count", 0)
    if word_count > 40:
        issues.append(f"Word count={word_count} — cut to ≤35 words, replace text with visual encoding")

    if not issues:
        issues.append("Minor refinements — increase visual polish and channel congruence")

    # Top 3 issues as intent
    top_issues = issues[:3]
    intent = "Fix these issues:\n" + "\n".join(f"- {i}" for i in top_issues)
    return intent


def auto_improve(image_path, abstract=None, max_turns=5,
                 target_archetype="cristallin", output_dir=None,
                 ga_image_id=None):
    """Run the autonomous improvement loop.

    Args:
        image_path: Path to the GA image
        abstract: Optional paper abstract text
        max_turns: Maximum iterations (default 5)
        target_archetype: Stop when this archetype is reached
        output_dir: Where to save turn logs (default: data/auto_improve/)

    Returns:
        dict with turn history and final state
    """
    from vision_scorer import analyze_ga_image
    from channel_analyzer import analyze_ga_channels
    from archetype import classify_from_vision_metadata, ARCHETYPES
    from ga_advisor import advise

    if output_dir is None:
        slug = os.path.splitext(os.path.basename(image_path))[0]
        output_dir = os.path.join(_HERE, "data", "auto_improve", slug)
    os.makedirs(output_dir, exist_ok=True)

    # Load image
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}

    history = []
    prev_score = None
    plateau_count = 0

    for turn in range(1, max_turns + 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"TURN {turn}/{max_turns}")
        logger.info(f"{'='*60}")

        turn_data = {"turn": turn, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}

        # ── Step 1: Analyze ──
        logger.info("Step 1: Vision analysis...")
        try:
            result = analyze_ga_image(image_bytes, filename=f"auto_t{turn}.png")
            meta = result["metadata"]
            graph_path = result["saved_path"]
            turn_data["graph_path"] = graph_path
            turn_data["node_count"] = len(result["graph"]["nodes"])
            turn_data["link_count"] = len(result["graph"]["links"])
            turn_data["word_count"] = meta.get("word_count", 0)
            turn_data["hierarchy_clear"] = meta.get("hierarchy_clear", False)
            turn_data["executive_summary"] = meta.get("executive_summary_fr", "")
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            turn_data["error"] = f"vision: {e}"
            history.append(turn_data)
            break

        # ── Step 2: Channel analysis ──
        logger.info("Step 2: Channel analysis...")
        time.sleep(3)
        try:
            enriched = analyze_ga_channels(image_path, graph_path)
            ca = enriched.get("metadata", {}).get("channel_analysis", {})
            turn_data["channels_used"] = ca.get("channels_used", 0)
            turn_data["avg_effectiveness"] = ca.get("avg_effectiveness", 0)
            turn_data["anti_patterns"] = enriched.get("metadata", {}).get("anti_patterns", [])
            turn_data["anti_pattern_count"] = len(turn_data["anti_patterns"])

            # Low-effectiveness channels
            details = enriched.get("metadata", {}).get("channel_details", [])
            turn_data["low_channels"] = [
                c for c in details
                if c.get("used") and c.get("effectiveness", 1) < 0.5
            ]
        except Exception as e:
            logger.warning(f"Channel analysis failed (non-blocking): {e}")
            turn_data["channels_used"] = 0
            turn_data["avg_effectiveness"] = 0
            turn_data["anti_patterns"] = []
            turn_data["anti_pattern_count"] = 0
            turn_data["low_channels"] = []

        # ── Step 3: Archetype classification ──
        logger.info("Step 3: Archetype classification...")
        arch = classify_from_vision_metadata(meta)
        info = ARCHETYPES.get(arch["archetype"], {})
        scores = arch.get("approximated_scores", {})
        turn_data["archetype"] = arch["archetype"]
        turn_data["archetype_name"] = info.get("name_fr", "?")
        turn_data["confidence"] = arch["confidence"]
        turn_data["s9b"] = scores.get("s9b", 0)
        turn_data["s10"] = scores.get("s10", 0)

        # Composite score for comparison
        current_score = (
            turn_data["s9b"] * 0.4 +
            turn_data["avg_effectiveness"] * 0.3 +
            (1 if turn_data["hierarchy_clear"] else 0) * 0.2 +
            max(0, 1 - turn_data["word_count"] / 50) * 0.1
        )
        turn_data["composite_score"] = round(current_score, 3)

        # ── Log turn ──
        logger.info(f"  Archetype: {turn_data['archetype_name']} ({turn_data['confidence']:.0%})")
        logger.info(f"  S9b={turn_data['s9b']} | S10={turn_data['s10']} | Words={turn_data['word_count']}")
        logger.info(f"  Channels: {turn_data['channels_used']} used, avg eff {turn_data['avg_effectiveness']:.2f}")
        logger.info(f"  Anti-patterns: {turn_data['anti_pattern_count']}")
        logger.info(f"  Composite: {current_score:.3f}")

        if prev_score is not None:
            delta = current_score - prev_score
            turn_data["delta"] = round(delta, 3)
            logger.info(f"  Delta: {'+' if delta >= 0 else ''}{delta:.3f}")
        else:
            turn_data["delta"] = None

        history.append(turn_data)

        # ── Check stop conditions ──

        # Target archetype reached
        if arch["archetype"] == target_archetype:
            logger.info(f"\n🎯 TARGET REACHED: {target_archetype} at turn {turn}")
            break

        # Plateau detection
        if prev_score is not None:
            delta = current_score - prev_score
            if abs(delta) < 0.02:
                plateau_count += 1
                if plateau_count >= 2:
                    logger.info(f"\n📊 PLATEAU: score stable for {plateau_count} turns, stopping")
                    break
            else:
                plateau_count = 0

        # All anti-patterns resolved
        if turn_data["anti_pattern_count"] == 0 and turn_data["avg_effectiveness"] >= 0.8:
            logger.info(f"\n✅ ALL CLEAN: no anti-patterns, high effectiveness")
            break

        # Last turn — don't advise
        if turn >= max_turns:
            logger.info(f"\n⏰ MAX TURNS ({max_turns}) reached")
            break

        # ── Step 4: Generate improvement intent ──
        intent = _build_intent_from_diagnosis(turn_data)
        turn_data["intent"] = intent
        logger.info(f"Step 4: Advising with intent:\n{intent}")

        # ── Step 5: Get advised graph ──
        time.sleep(3)
        try:
            advised = advise(image_path, graph_path, intent,
                             output_path=os.path.join(output_dir, f"turn_{turn}_advised.yaml"))
            if advised:
                # Count changes
                changes = [n for n in advised.get("nodes", []) if n.get("_change")]
                turn_data["changes_made"] = len(changes)
                turn_data["changes"] = [
                    {"node": n.get("name", ""), "change": n.get("_change", "")}
                    for n in changes
                ]
                logger.info(f"  {len(changes)} changes proposed")
                for c in changes[:3]:
                    logger.info(f"    ~ {c.get('name','')}: {c.get('_change','')[:60]}")
            else:
                turn_data["changes_made"] = 0
                turn_data["changes"] = []
                logger.warning("  Advisor returned None")
        except Exception as e:
            logger.warning(f"  Advisor failed: {e}")
            turn_data["changes_made"] = 0
            turn_data["changes"] = []

        # ── Step 6: Compute graph stats + Log turn to DB ──
        nodes = result["graph"]["nodes"]
        resolved = sum(1 for n in nodes if n.get("energy", 1) < 0.5)
        high_e = sum(1 for n in nodes if n.get("energy", 0) >= 0.7)
        avg_w = sum(n.get("weight", 0) for n in nodes) / len(nodes) if nodes else 0
        avg_e = sum(n.get("energy", 0) for n in nodes) / len(nodes) if nodes else 0

        ap = turn_data.get("anti_patterns", [])
        n_fragile = sum(1 for a in ap if a.get("type") == "fragile")
        n_incong = sum(1 for a in ap if a.get("type") == "incongruent")
        n_inverse = sum(1 for a in ap if a.get("type") == "inverse")
        n_missing = sum(1 for a in ap if a.get("type") == "missing_category")

        turn_data.update({
            "resolved_nodes": resolved,
            "high_energy_nodes": high_e,
            "avg_node_weight": round(avg_w, 3),
            "avg_node_energy": round(avg_e, 3),
        })

        try:
            from db import get_db
            db = get_db()
            db.execute("""INSERT INTO improvement_runs
                (ga_image_id, turn, archetype, archetype_confidence,
                 s9b, s10, composite_score, word_count,
                 channels_used, avg_effectiveness, anti_pattern_count,
                 hierarchy_clear, delta, intent, changes_made,
                 node_count, link_count, resolved_nodes, high_energy_nodes,
                 avg_node_weight, avg_node_energy, dominant_encoding,
                 color_count, executive_summary,
                 fragile_count, incongruent_count, inverse_count,
                 missing_category_count)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (ga_image_id, turn, turn_data.get("archetype"),
                 turn_data.get("confidence"),
                 turn_data.get("s9b"), turn_data.get("s10"),
                 turn_data.get("composite_score"),
                 turn_data.get("word_count"), turn_data.get("channels_used"),
                 turn_data.get("avg_effectiveness"),
                 turn_data.get("anti_pattern_count"),
                 1 if turn_data.get("hierarchy_clear") else 0,
                 turn_data.get("delta"),
                 turn_data.get("intent", ""),
                 turn_data.get("changes_made", 0),
                 turn_data.get("node_count"), turn_data.get("link_count"),
                 resolved, high_e, round(avg_w, 3), round(avg_e, 3),
                 meta.get("dominant_encoding", ""),
                 meta.get("color_count", 0),
                 meta.get("executive_summary_fr", "")[:500],
                 n_fragile, n_incong, n_inverse, n_missing))
            db.commit()
            db.close()
        except Exception as e:
            logger.warning(f"  DB logging failed (non-blocking): {e}")

        prev_score = current_score

        # Rate limit between turns
        if turn < max_turns:
            logger.info("  Waiting 5s before next turn...")
            time.sleep(5)

    # ── Final report ──
    report = {
        "image": os.path.basename(image_path),
        "total_turns": len(history),
        "max_turns": max_turns,
        "target_archetype": target_archetype,
        "abstract_provided": abstract is not None,
        "history": history,
    }

    if history:
        first = history[0]
        last = history[-1]
        report["summary"] = {
            "start_archetype": first.get("archetype_name", "?"),
            "end_archetype": last.get("archetype_name", "?"),
            "start_composite": first.get("composite_score", 0),
            "end_composite": last.get("composite_score", 0),
            "total_delta": round(
                last.get("composite_score", 0) - first.get("composite_score", 0), 3
            ),
            "start_anti_patterns": first.get("anti_pattern_count", 0),
            "end_anti_patterns": last.get("anti_pattern_count", 0),
            "start_s9b": first.get("s9b", 0),
            "end_s9b": last.get("s9b", 0),
            "reached_target": last.get("archetype") == target_archetype,
        }

    # Save report
    report_path = os.path.join(output_dir, "report.yaml")
    with open(report_path, "w", encoding="utf-8") as f:
        yaml.dump(report, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"\nReport saved: {report_path}")

    # Save evolution CSV for easy plotting
    csv_path = os.path.join(output_dir, "evolution.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("turn,archetype,s9b,s10,composite,word_count,channels_used,avg_effectiveness,anti_patterns,hierarchy_clear,delta\n")
        for t in history:
            f.write(f"{t.get('turn',0)},"
                    f"{t.get('archetype','')},"
                    f"{t.get('s9b',0)},"
                    f"{t.get('s10',0)},"
                    f"{t.get('composite_score',0)},"
                    f"{t.get('word_count',0)},"
                    f"{t.get('channels_used',0)},"
                    f"{t.get('avg_effectiveness',0):.3f},"
                    f"{t.get('anti_pattern_count',0)},"
                    f"{1 if t.get('hierarchy_clear') else 0},"
                    f"{t.get('delta','')}\n")
    logger.info(f"Evolution CSV: {csv_path}")

    # Print summary
    if "summary" in report:
        s = report["summary"]
        print(f"\n{'='*50}")
        print(f"AUTO-IMPROVE COMPLETE — {len(history)} turns")
        print(f"{'='*50}")
        print(f"Archetype: {s['start_archetype']} → {s['end_archetype']}")
        print(f"Composite: {s['start_composite']:.3f} → {s['end_composite']:.3f} (Δ {s['total_delta']:+.3f})")
        print(f"S9b: {s['start_s9b']} → {s['end_s9b']}")
        print(f"Anti-patterns: {s['start_anti_patterns']} → {s['end_anti_patterns']}")
        print(f"Target reached: {'YES' if s['reached_target'] else 'NO'}")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GA Auto-Improve — autonomous iteration loop")
    parser.add_argument("image", help="Path to GA image")
    parser.add_argument("--abstract", help="Paper abstract text")
    parser.add_argument("--abstract-file", help="Path to file containing abstract")
    parser.add_argument("--max-turns", type=int, default=5, help="Max iterations (default 5)")
    parser.add_argument("--target-archetype", default="cristallin",
                        help="Stop when this archetype is reached (default: cristallin)")
    parser.add_argument("--output-dir", help="Output directory for turn logs")
    args = parser.parse_args()

    abstract = _load_abstract(args.abstract, args.abstract_file)

    parser.add_argument("--ga-id", type=int, help="GA image ID in database (for tracking)")

    args = parser.parse_args()
    abstract = _load_abstract(args.abstract, args.abstract_file)

    auto_improve(
        args.image,
        abstract=abstract,
        max_turns=args.max_turns,
        target_archetype=args.target_archetype,
        output_dir=args.output_dir,
        ga_image_id=getattr(args, 'ga_id', None),
    )
