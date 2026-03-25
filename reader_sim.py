"""
Reader Simulation — Proportional attention model with debug trace.

Simulates how a reader's eye moves through a GA in 5 seconds.
The reader is an ACTOR with finite attention budget.

Algorithm V1 (proportional):
  - Total budget = total_ticks (50 = 5s at 100ms/tick)
  - Each thing node gets ideal_ticks proportional to its weight
  - Actor visits things in Z-order (by estimated position: top→bottom, left→right)
  - Moving between nodes costs 1 tick per saccade
  - At each node, fixation propagates attention to linked narratives
  - If time runs out → remaining nodes = PREDICTED DEAD ZONES

Later: test physics on top (distance-based saccade cost, fatigue, etc.)

Debug mode (--debug):
  Shows every intermediate state:
  - Allocation plan (ideal vs available)
  - Each tick: position, action (saccade/fixation), attention flow
  - Narrative propagation events
  - Final accounting: plan vs actual

Usage:
    python reader_sim.py <graph.yaml> [--ticks 50] [--debug] [--verbose]
"""

import yaml
import json
import math
import os
import sys
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("reader_sim")


# ── Layout estimation ────────────────────────────────────────────────

def _estimate_positions(graph):
    """Get positions for nodes — prefer bbox from Gemini, fallback to estimation.

    If nodes have a `bbox` field [x, y, w, h] (normalized 0-1), use the center
    of the bbox as position. Otherwise, estimate from graph structure.

    Returns: dict of node_id → (x, y) normalized to [0, 1]
    """
    # First pass: extract positions from bbox where available
    bbox_positions = {}
    for node in graph.get("nodes", []):
        bbox = node.get("bbox")
        if bbox and isinstance(bbox, list) and len(bbox) == 4:
            try:
                x, y, w, h = [float(v) for v in bbox]
                # Center of bbox
                cx = min(1, max(0, x + w / 2))
                cy = min(1, max(0, y + h / 2))
                bbox_positions[node["id"]] = (cx, cy)
            except (ValueError, TypeError):
                pass

    # If all nodes have bbox, skip estimation entirely
    all_ids = {n["id"] for n in graph.get("nodes", [])}
    if all_ids and all_ids <= set(bbox_positions.keys()):
        return bbox_positions
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])

    # Build containment: which things are in which spaces
    space_children = defaultdict(list)
    for link in links:
        src = link.get("source", "")
        tgt = link.get("target", "")
        # thing → space = containment
        if src.startswith("thing:") and tgt.startswith("space:"):
            space_children[tgt].append(src)
        elif src.startswith("space:") and tgt.startswith("thing:"):
            space_children[src].append(tgt)
        # narrative → space
        if src.startswith("narrative:") and tgt.startswith("space:"):
            space_children[tgt].append(src)
        elif src.startswith("space:") and tgt.startswith("narrative:"):
            space_children[src].append(tgt)

    positions = {}
    spaces = [n for n in nodes if n.get("node_type") == "space"]
    non_spaces = [n for n in nodes if n.get("node_type") != "space"]

    # Layout spaces in a grid (Z-pattern)
    n_spaces = max(len(spaces), 1)
    cols = min(n_spaces, 3)  # max 3 columns
    rows = math.ceil(n_spaces / cols)

    for i, space in enumerate(spaces):
        col = i % cols
        row = i // cols
        # Center of each space cell
        cx = (col + 0.5) / cols
        cy = (row + 0.5) / rows
        positions[space["id"]] = (cx, cy)

        # Position children within the space cell
        children = space_children.get(space["id"], [])
        for j, child_id in enumerate(children):
            # Distribute children in a small cluster around space center
            angle = 2 * math.pi * j / max(len(children), 1)
            spread = 0.3 / cols  # cluster radius
            child_x = cx + spread * math.cos(angle)
            child_y = cy + spread * math.sin(angle)
            positions[child_id] = (
                max(0, min(1, child_x)),
                max(0, min(1, child_y)),
            )

    # Position orphan nodes (not in any space) along the bottom
    orphans = [n for n in non_spaces if n["id"] not in positions]
    for i, node in enumerate(orphans):
        positions[node["id"]] = (
            (i + 0.5) / max(len(orphans), 1),
            0.9,
        )

    # Override estimated positions with bbox-derived positions where available
    positions.update(bbox_positions)

    return positions


# ── Z-order sorting ──────────────────────────────────────────────────

def _z_order_key(node_id, positions):
    """Sort key for Z-pattern: top→bottom (y), then left→right (x)."""
    pos = positions.get(node_id, (0.5, 0.5))
    # Quantize y into rows (3 rows) to get proper Z-scan lines
    row = int(pos[1] * 3)
    return (row, pos[0])


# ── Core simulation ──────────────────────────────────────────────────

def simulate_reading(graph, total_ticks=50, tick_ms=100, verbose=False, debug=False,
                     mode="system1"):
    """Simulate a reader scanning a GA with proportional attention allocation.

    V1 Algorithm:
    1. Compute ideal fixation ticks per thing, proportional to weight
    2. Sort things in Z-order (by position)
    3. Visit sequentially: 1 tick saccade + N ticks fixation per node
    4. During fixation: propagate attention to linked narratives
    5. Time runs out → remaining nodes never visited = dead zones

    Modes:
        system1: 5 seconds (50 ticks), attention=1.0, glance reading
        system2: 90 seconds (900 ticks), attention=1.5, deliberate reading
                 Higher attention = deeper processing per fixation

    Args:
        graph: L3 graph dict (nodes, links, metadata)
        total_ticks: number of simulation steps (50 = 5s, 900 = 90s)
        tick_ms: milliseconds per tick
        verbose: log summary per node visit
        debug: full tick-by-tick trace with intermediate states
        mode: "system1" (glance) or "system2" (deliberate)

    Returns:
        dict with scanpath, narrative_attention, node_heatmap, dead_zones, stats, debug_trace
    """
    # System 2: deliberate reading → higher attention injection
    if mode == "system2":
        total_ticks = max(total_ticks, 900)  # 90 seconds minimum
    base_attention = 1.5 if mode == "system2" else 1.0
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])

    node_lookup = {n["id"]: n for n in nodes}
    positions = _estimate_positions(graph)

    # Build adjacency
    adj = defaultdict(list)
    for link in links:
        src = link.get("source", "")
        tgt = link.get("target", "")
        w = link.get("weight", 0.5)
        adj[src].append((tgt, w))
        adj[tgt].append((src, w))

    # Separate node types
    things = [n for n in nodes if n.get("node_type") == "thing"]
    spaces = [n for n in nodes if n.get("node_type") == "space"]
    narratives = [n for n in nodes if n.get("node_type") == "narrative"]

    if not things:
        return {"error": "No thing nodes to visit"}

    # ── ANTI-PATTERN INDEX (from enriched graphs) ──
    # Read anti-patterns from metadata if available
    anti_patterns_by_node = defaultdict(list)
    for ap in graph.get("metadata", {}).get("channel_analysis", {}).get("anti_patterns", []):
        nid = ap.get("node_id")
        if nid:
            anti_patterns_by_node[nid].append(ap.get("type", ""))

    # ── PLAN: compute ideal allocation ──

    # Sort things in Z-order
    things_z = sorted(things, key=lambda t: _z_order_key(t["id"], positions))

    total_weight = sum(t.get("weight", 0.5) for t in things_z)
    if total_weight == 0:
        total_weight = len(things_z)

    # Saccade budget: 1 tick per transition (n_things - 1 saccades)
    n_saccades = len(things_z) - 1
    fixation_budget = total_ticks - n_saccades

    if fixation_budget <= 0:
        # More things than ticks — can't even visit all
        fixation_budget = total_ticks
        # Will run out before visiting everything

    # Ideal fixation ticks per thing (proportional to weight)
    plan = []
    for thing in things_z:
        w = thing.get("weight", 0.5)
        ideal = fixation_budget * w / total_weight
        plan.append({
            "node_id": thing["id"],
            "node_name": thing.get("name", ""),
            "weight": w,
            "ideal_ticks": round(ideal, 2),
            "allocated_ticks": max(1, round(ideal)),  # at least 1 tick fixation
            "position": positions.get(thing["id"], (0.5, 0.5)),
        })

    # Adjust allocations to fit budget (rounding may overshoot)
    total_allocated = sum(p["allocated_ticks"] for p in plan)
    while total_allocated > fixation_budget and plan:
        # Trim from lowest-weight node
        min_node = min(plan, key=lambda p: p["weight"])
        if min_node["allocated_ticks"] > 1:
            min_node["allocated_ticks"] -= 1
            total_allocated -= 1
        else:
            break

    # Debug trace
    trace = []

    if debug:
        trace.append({
            "phase": "PLAN",
            "total_ticks": total_ticks,
            "total_things": len(things_z),
            "saccade_budget": n_saccades,
            "fixation_budget": fixation_budget,
            "total_weight": round(total_weight, 3),
            "allocation": [
                {
                    "node": p["node_name"],
                    "weight": p["weight"],
                    "ideal": p["ideal_ticks"],
                    "allocated": p["allocated_ticks"],
                    "pos": f"({p['position'][0]:.2f}, {p['position'][1]:.2f})",
                }
                for p in plan
            ],
        })

    # ── EXECUTE: visit nodes in Z-order ──

    tick = 0
    actor_pos = (0.05, 0.05)  # start top-left
    actor_attention = base_attention
    visit_count = defaultdict(int)
    node_attention = defaultdict(float)
    narrative_attention = defaultdict(float)
    scanpath = []
    visited_set = set()
    skipped_nodes = []

    for node_idx, p in enumerate(plan):
        tid = p["node_id"]
        thing = node_lookup[tid]
        target_pos = p["position"]

        # ── SACCADE: move to this node (costs 1 tick, except for first node) ──
        if node_idx > 0:
            if tick >= total_ticks:
                # Out of time — this node and all remaining are dead
                skipped_nodes.append(p)
                if debug:
                    trace.append({
                        "phase": "TIMEOUT",
                        "tick": tick,
                        "time_ms": tick * tick_ms,
                        "skipped_node": p["node_name"],
                        "reason": f"Budget exhausted at tick {tick}/{total_ticks}",
                        "remaining_nodes": len(plan) - node_idx,
                    })
                continue

            # Saccade distance
            dx = target_pos[0] - actor_pos[0]
            dy = target_pos[1] - actor_pos[1]
            dist = math.sqrt(dx * dx + dy * dy)

            if debug:
                trace.append({
                    "phase": "SACCADE",
                    "tick": tick,
                    "time_ms": tick * tick_ms,
                    "from": f"({actor_pos[0]:.2f}, {actor_pos[1]:.2f})",
                    "to": f"({target_pos[0]:.2f}, {target_pos[1]:.2f})",
                    "target": p["node_name"],
                    "distance": round(dist, 3),
                    "attention_before": round(actor_attention, 4),
                })

            actor_pos = target_pos
            tick += 1  # saccade costs 1 tick

        else:
            # First node — no saccade cost, just jump there
            actor_pos = target_pos
            if debug:
                trace.append({
                    "phase": "START",
                    "tick": tick,
                    "time_ms": tick * tick_ms,
                    "first_node": p["node_name"],
                    "position": f"({target_pos[0]:.2f}, {target_pos[1]:.2f})",
                    "attention": round(actor_attention, 4),
                })

        # ── FIXATION: spend allocated ticks at this node ──
        allocated = p["allocated_ticks"]
        actual_fixation_ticks = 0

        for fix_tick in range(allocated):
            if tick >= total_ticks:
                break

            visit_count[tid] += 1
            actual_fixation_ticks += 1

            # Fixation strength = remaining attention * node weight
            fixation_strength = actor_attention * p["weight"]
            node_attention[tid] += fixation_strength

            # ── Anti-pattern penalties on narrative transmission ──
            # B3: Incongruent = contradictory signals → reader confused → halved transmission
            # B4: Fragile = single channel → vulnerable → discounted transmission
            transmission_efficiency = 1.0
            penalties_applied = []

            if "incongruent" in anti_patterns_by_node.get(tid, []):
                transmission_efficiency *= 0.5
                penalties_applied.append("incongruent(-50%)")

            n_channels = len(thing.get("visual_channels", []))
            if n_channels > 0:
                channel_robustness = min(n_channels / 3, 1.0)
                if channel_robustness < 1.0:
                    transmission_efficiency *= channel_robustness
                    penalties_applied.append(f"fragile({n_channels}ch→{channel_robustness:.0%})")

            # Propagate attention to linked narratives (with penalties)
            narr_events = []
            for neighbor, link_w in adj.get(tid, []):
                if neighbor.startswith("narrative:"):
                    transmitted = fixation_strength * link_w * transmission_efficiency
                    narrative_attention[neighbor] += transmitted
                    narr_events.append({
                        "narrative": node_lookup.get(neighbor, {}).get("name", neighbor),
                        "link_weight": link_w,
                        "transmitted": round(transmitted, 4),
                        "penalties": penalties_applied if penalties_applied else None,
                    })

            scanpath.append({
                "tick": tick,
                "time_ms": tick * tick_ms,
                "node_id": tid,
                "node_name": thing.get("name", ""),
                "action": "fixation",
                "fixation_tick": fix_tick + 1,
                "x": round(target_pos[0], 3),
                "y": round(target_pos[1], 3),
                "attention": round(actor_attention, 4),
                "fixation": round(fixation_strength, 4),
            })

            if debug:
                entry = {
                    "phase": "FIXATION",
                    "tick": tick,
                    "time_ms": tick * tick_ms,
                    "node": p["node_name"],
                    "fixation_tick": f"{fix_tick + 1}/{allocated}",
                    "attention": round(actor_attention, 4),
                    "fixation_strength": round(fixation_strength, 4),
                    "node_attention_total": round(node_attention[tid], 4),
                }
                if narr_events:
                    entry["narrative_propagation"] = narr_events
                trace.append(entry)

            tick += 1

        visited_set.add(tid)

        # Node visit summary
        if verbose:
            logger.info(
                f"  [{node_idx+1}/{len(plan)}] {p['node_name'][:35]:35s} | "
                f"w={p['weight']:.2f} | {actual_fixation_ticks}/{allocated} ticks | "
                f"att_total={node_attention[tid]:.3f}")

        if debug and actual_fixation_ticks < allocated:
            trace.append({
                "phase": "TRUNCATED",
                "tick": tick,
                "node": p["node_name"],
                "planned": allocated,
                "actual": actual_fixation_ticks,
                "reason": "Budget exhausted mid-fixation",
            })

        # Check remaining nodes that will be skipped
        if tick >= total_ticks and node_idx < len(plan) - 1:
            for remaining in plan[node_idx + 1:]:
                skipped_nodes.append(remaining)
                if debug:
                    trace.append({
                        "phase": "TIMEOUT",
                        "tick": tick,
                        "skipped_node": remaining["node_name"],
                        "weight": remaining["weight"],
                        "reason": "Never reached — budget exhausted",
                    })
            break

    # ── RESULTS ──

    # Normalize narrative attention
    max_narr = max(narrative_attention.values()) if narrative_attention else 1
    normalized_narrative = {
        nid: round(v / max(max_narr, 0.01), 3)
        for nid, v in narrative_attention.items()
    }

    # Dead zones: spaces where no child thing was visited
    visited_spaces = set()
    for link in links:
        src, tgt = link.get("source", ""), link.get("target", "")
        if src in node_attention and tgt.startswith("space:"):
            visited_spaces.add(tgt)
        if tgt in node_attention and src.startswith("space:"):
            visited_spaces.add(src)

    dead_spaces = [
        {"id": s["id"], "name": s["name"]}
        for s in spaces if s["id"] not in visited_spaces
    ]

    # Orphan narratives: messages that received zero attention
    orphan_narratives = [
        {"id": n["id"], "name": n["name"]}
        for n in narratives if n["id"] not in narrative_attention
    ]

    # Heatmap: nodes by attention
    heatmap = sorted(
        [{"id": nid, "name": node_lookup.get(nid, {}).get("name", ""),
          "attention": round(att, 4), "visits": visit_count[nid],
          "pct": round(att / max(sum(node_attention.values()), 0.01), 3)}
         for nid, att in node_attention.items()],
        key=lambda x: -x["attention"]
    )

    # Plan vs actual comparison
    plan_vs_actual = []
    for p in plan:
        tid = p["node_id"]
        actual_visits = visit_count.get(tid, 0)
        was_visited = tid in visited_set
        plan_vs_actual.append({
            "node": p["node_name"],
            "weight": p["weight"],
            "planned_ticks": p["allocated_ticks"],
            "actual_ticks": actual_visits,
            "attention_received": round(node_attention.get(tid, 0), 4),
            "status": "visited" if was_visited else "SKIPPED",
            "deficit": p["allocated_ticks"] - actual_visits,
        })

    # Overall transmission score
    if narratives:
        coverage = sum(1 for n in narratives if n["id"] in narrative_attention) / len(narratives)
        avg_attention = sum(normalized_narrative.values()) / len(narratives) if narratives else 0
    else:
        coverage = 0
        avg_attention = 0

    # Complexity indicator: how much budget pressure
    budget_pressure = (n_saccades + total_allocated) / max(total_ticks, 1)
    # >1 means the GA has more content than 5 seconds can cover

    result = {
        "scanpath": scanpath,
        "narrative_attention": normalized_narrative,
        "narrative_details": [
            {
                "id": n["id"],
                "name": n["name"],
                "received": normalized_narrative.get(n["id"], 0),
                "status": "reached" if n["id"] in narrative_attention else "missed",
            }
            for n in narratives
        ],
        "heatmap": heatmap,
        "dead_spaces": dead_spaces,
        "orphan_narratives": orphan_narratives,
        "skipped_nodes": [
            {"name": s["node_name"], "weight": s["weight"]}
            for s in skipped_nodes
        ],
        "plan_vs_actual": plan_vs_actual,
        "stats": {
            "mode": mode,
            "total_ticks": tick,
            "total_time_ms": tick * tick_ms,
            "unique_nodes_visited": len(visited_set),
            "total_things": len(things),
            "nodes_skipped": len(skipped_nodes),
            "narrative_coverage": round(coverage, 3),
            "avg_narrative_attention": round(avg_attention, 3),
            "attention_remaining": round(actor_attention, 4),
            "dead_space_count": len(dead_spaces),
            "orphan_narrative_count": len(orphan_narratives),
            "budget_pressure": round(budget_pressure, 3),
            "complexity_verdict": (
                "OK" if budget_pressure <= 0.8 else
                "DENSE" if budget_pressure <= 1.0 else
                "OVERLOADED"
            ),
        },
        "recommendations": (recs := _generate_prompts(
            dead_spaces, orphan_narratives, heatmap, normalized_narrative,
            narratives, skipped_nodes, budget_pressure
        )),
        # Flat text list for backward compat (auto-improve intent, CLI)
        "prompts": [r["text"] for r in recs],
    }

    if debug:
        # Add final accounting to trace
        trace.append({
            "phase": "FINAL_ACCOUNTING",
            "ticks_used": tick,
            "ticks_total": total_ticks,
            "budget_pressure": round(budget_pressure, 3),
            "nodes_visited": len(visited_set),
            "nodes_skipped": len(skipped_nodes),
            "narratives_reached": sum(1 for n in narratives if n["id"] in narrative_attention),
            "narratives_total": len(narratives),
            "plan_vs_actual": plan_vs_actual,
        })
        result["debug_trace"] = trace

    return result


def _generate_prompts(dead_spaces, orphan_narratives, heatmap, narrative_attention,
                      narratives, skipped_nodes, budget_pressure):
    """Generate structured recommendations from simulation results.

    Each recommendation is a dict with:
      - source: what simulation finding triggered this (links to narrative)
      - finding: the factual observation (FACT)
      - problem: why this matters (PROBLEM)
      - question: open question for improvement (QUESTION)
      - text: full text (FACT → PROBLEM → QUESTION concatenated)
    """
    recs = []

    # Budget overload
    if budget_pressure > 1.0:
        recs.append({
            "source": "budget_overload",
            "finding": f"Pression={budget_pressure:.1f}x — {len(skipped_nodes)} éléments jamais vus.",
            "problem": "Le visuel contient plus de contenu que le lecteur ne peut absorber.",
            "question": "Quels éléments peuvent être fusionnés ou supprimés sans perdre de message ?",
        })

    # Dead spaces
    for ds in dead_spaces:
        recs.append({
            "source": f"dead_space:{ds['id']}",
            "finding": f"La zone '{ds['name']}' n'a reçu aucune attention du lecteur.",
            "problem": "Son contenu est invisible dans le temps imparti.",
            "question": "Qu'est-ce qui attirerait le regard vers cette zone ?",
        })

    # Skipped nodes
    for sn in skipped_nodes[:3]:
        recs.append({
            "source": f"skipped_node:{sn['name']}",
            "finding": f"L'élément '{sn['name']}' (poids={sn['weight']}) n'a pas été lu par le lecteur (pas le temps).",
            "problem": "Le lecteur a épuisé son budget attentionnel avant d'y arriver.",
            "question": "Comment le rendre prioritaire ou l'intégrer à un élément déjà vu ?",
        })

    # Orphan narratives
    for on in orphan_narratives:
        recs.append({
            "source": f"orphan_narrative:{on['id']}",
            "finding": f"Le message '{on['name']}' n'a reçu aucune attention.",
            "problem": "Aucun élément visuel ne transmet ce message au lecteur.",
            "question": "Quel élément concret porterait ce message ?",
        })

    # Narratives with low attention
    for n in narratives:
        att = narrative_attention.get(n["id"], 0)
        if 0 < att < 0.3:
            recs.append({
                "source": f"weak_narrative:{n['id']}",
                "finding": f"Le message '{n['name']}' ne reçoit que {att:.0%} de l'attention.",
                "problem": "Les éléments qui le portent sont soit trop petits, soit mal positionnés.",
                "question": "Comment renforcer la transmission vers ce message ?",
            })

    # Attention concentration (top node gets >50% of total)
    if heatmap and len(heatmap) > 1:
        total_att = sum(h["attention"] for h in heatmap)
        if total_att > 0:
            top_pct = heatmap[0]["attention"] / total_att
            if top_pct > 0.5:
                recs.append({
                    "source": f"attention_monopoly:{heatmap[0]['id']}",
                    "finding": f"'{heatmap[0]['name']}' absorbe {top_pct:.0%} de l'attention totale.",
                    "problem": "Les autres éléments sont écrasés.",
                    "question": "Comment redistribuer le poids visuel sans perdre ce point focal ?",
                })

    # Build full text for each rec
    for r in recs:
        r["text"] = f"{r['finding']} {r['problem']} {r['question']}"

    return recs


# ── Narrative generator ──────────────────────────────────────────────

def generate_reading_narrative(result, graph):
    """Generate a human-readable narrative of the simulated reading experience.

    Takes the simulation result and the original graph, produces a
    paragraph-by-paragraph story of what the reader saw, understood,
    missed, and why.
    """
    stats = result["stats"]
    scanpath = result["scanpath"]
    heatmap = result["heatmap"]
    narrative_details = result.get("narrative_details", [])
    dead_spaces = result.get("dead_spaces", [])
    skipped = result.get("skipped_nodes", [])
    plan_vs_actual = result.get("plan_vs_actual", [])

    nodes = graph.get("nodes", [])
    links = graph.get("links", [])
    node_lookup = {n["id"]: n for n in nodes}

    # Build space→things and space→narratives maps
    adj = defaultdict(list)
    for link in links:
        src = link.get("source", "")
        tgt = link.get("target", "")
        adj[src].append(tgt)
        adj[tgt].append(src)

    space_things = defaultdict(list)
    space_narratives = defaultdict(list)
    thing_space = {}
    for link in links:
        src, tgt = link.get("source", ""), link.get("target", "")
        if src.startswith("thing:") and tgt.startswith("space:"):
            space_things[tgt].append(src)
            thing_space[src] = tgt
        elif src.startswith("space:") and tgt.startswith("thing:"):
            space_things[src].append(tgt)
            thing_space[tgt] = src
        if src.startswith("narrative:") and tgt.startswith("space:"):
            space_narratives[tgt].append(src)
        elif src.startswith("space:") and tgt.startswith("narrative:"):
            space_narratives[src].append(tgt)

    # Node attention from heatmap
    node_att = {h["id"]: h for h in heatmap}

    # Narrative results
    narr_reached = [n for n in narrative_details if n["status"] == "reached"]
    narr_missed = [n for n in narrative_details if n["status"] == "missed"]

    paragraphs = []

    # ── Opening: overall verdict ──
    visited = stats["unique_nodes_visited"]
    total = stats["total_things"]
    n_skipped = stats["nodes_skipped"]
    pressure = stats["budget_pressure"]
    verdict = stats["complexity_verdict"]

    mode = stats.get("mode", "system1")
    time_str = f"{stats['total_time_ms'] / 1000:.0f} secondes"

    # Count truly unread: skipped + truncated (0 actual ticks)
    unread = n_skipped
    for p in result.get("plan_vs_actual", []):
        if p["status"] == "visited" and p["actual_ticks"] == 0:
            unread += 1

    if verdict == "OVERLOADED":
        if unread > 0:
            opening = (
                f"Ce visuel est surchargé. Le lecteur a parcouru {visited} éléments sur {total} "
                f"en {time_str}, mais la densité d'information (pression={pressure:.2f}x) "
                f"l'a empêché de lire {unread} éléments.")
        else:
            opening = (
                f"Ce visuel est à la limite de la surcharge (pression={pressure:.2f}x). "
                f"Le lecteur a parcouru les {total} éléments en {time_str} "
                f"mais les derniers éléments ont reçu une attention minimale.")
    elif verdict == "DENSE":
        opening = (
            f"Ce visuel est dense mais lisible. Le lecteur a pu parcourir "
            f"{visited}/{total} éléments en {time_str}, avec une pression de {pressure:.2f}x "
            f"sur le budget attentionnel.")
    else:
        opening = (
            f"Ce visuel est bien calibré. Le lecteur a parcouru l'ensemble des "
            f"{total} éléments en {time_str} sans pression excessive "
            f"(pression={pressure:.2f}x).")
    if mode == "system2":
        opening += " (lecture délibérée System 2 — attention renforcée)"
    paragraphs.append(opening)

    # ── Scanpath story: what was seen first ──
    if scanpath:
        first = scanpath[0]
        # Count consecutive ticks on first node
        first_ticks = sum(1 for s in scanpath if s["node_id"] == first["node_id"]
                         and s == scanpath[scanpath.index(s)])
        first_count = 0
        for s in scanpath:
            if s["node_id"] == first["node_id"]:
                first_count += 1
            else:
                break

        tick_ms = stats.get("total_time_ms", 5000) / max(stats.get("total_ticks", 50), 1)
        entry = f"Le regard entre par '{first['node_name']}'"
        space_id = thing_space.get(first["node_id"])
        if space_id:
            space_name = node_lookup.get(space_id, {}).get("name", space_id)
            entry += f" dans la zone '{space_name}'"
        entry += f", qui reçoit {first_count * tick_ms:.0f}ms d'attention."
        paragraphs.append(entry)

    # ── Per-space traversal ──
    spaces = [n for n in nodes if n.get("node_type") == "space"]
    for space in spaces:
        sid = space["id"]
        sname = space["name"]
        things_in = space_things.get(sid, [])
        narrs_in = space_narratives.get(sid, [])

        if not things_in:
            continue

        # Check which things in this space were visited
        visited_things = [t for t in things_in if t in node_att]
        skipped_things = [t for t in things_in if t not in node_att]

        if not visited_things and not skipped_things:
            continue

        if sid in [ds["id"] for ds in dead_spaces]:
            paragraphs.append(
                f"La zone '{sname}' n'a jamais été atteinte par le regard. "
                f"Ses {len(things_in)} éléments sont invisibles.")
            continue

        # Build space paragraph
        parts = [f"Dans la zone '{sname}', "]

        # Top elements seen
        seen_names = []
        for tid in visited_things:
            name = node_lookup.get(tid, {}).get("name", tid)
            att = node_att.get(tid, {}).get("attention", 0)
            pct = node_att.get(tid, {}).get("pct", 0)
            visits = node_att.get(tid, {}).get("visits", 0)
            ms = visits * (stats.get("total_time_ms", 5000) / max(stats.get("total_ticks", 50), 1))
            seen_names.append(f"'{name}' ({ms:.0f}ms)")

        if seen_names:
            parts.append(f"le lecteur a fixé {', '.join(seen_names[:4])}")
            if len(seen_names) > 4:
                parts.append(f" et {len(seen_names)-4} autres")
            parts.append(". ")

        # Narratives in this space
        reached_in_space = []
        missed_in_space = []
        for nid in narrs_in:
            narr = next((n for n in narrative_details if n["id"] == nid), None)
            if narr:
                if narr["status"] == "reached":
                    reached_in_space.append(narr)
                else:
                    missed_in_space.append(narr)

        if reached_in_space:
            names = [f"'{n['name']}' ({n['received']:.0%})" for n in reached_in_space]
            parts.append(f"Le message {', '.join(names)} a été transmis. ")

        if missed_in_space:
            names = [f"'{n['name']}'" for n in missed_in_space]
            parts.append(
                f"En revanche, {', '.join(names)} n'a reçu aucune attention — "
                f"aucun élément visuel de cette zone ne porte ce message. ")

        if skipped_things:
            names = [node_lookup.get(t, {}).get("name", t) for t in skipped_things]
            quoted = [f"'{n}'" for n in names[:3]]
            parts.append(
                f"Les éléments {', '.join(quoted)} "
                f"n'ont pas été lus par le lecteur (pas le temps). ")

        paragraphs.append("".join(parts))

    # ── Orphan things (not in any space) ──
    orphan_things_visited = [
        p for p in plan_vs_actual
        if p["status"] == "visited" and not thing_space.get(
            next((n["id"] for n in nodes if n.get("name") == p["node"]), ""))
    ]

    # ── Narrative summary ──
    if narr_reached:
        strong = [n for n in narr_reached if n["received"] >= 0.7]
        weak = [n for n in narr_reached if 0 < n["received"] < 0.3]

        narr_parts = []
        if strong:
            names = [f"'{n['name']}'" for n in strong]
            narr_parts.append(
                f"Les messages {', '.join(names)} ont été bien transmis "
                f"(attention ≥ 70%)")
        if weak:
            names = [f"'{n['name']}' ({n['received']:.0%})" for n in weak]
            narr_parts.append(
                f"Les messages {', '.join(names)} ont été à peine perçus — "
                f"les éléments qui les portent sont trop faibles ou mal positionnés")

        if narr_parts:
            paragraphs.append(". ".join(narr_parts) + ".")

    if narr_missed:
        names = [f"'{n['name']}'" for n in narr_missed]
        total_narr = len(narrative_details)
        paragraphs.append(
            f"{len(narr_missed)}/{total_narr} messages n'ont reçu aucune attention : "
            f"{', '.join(names)}. "
            f"Ces messages n'ont pas de porteur visuel suffisant — "
            f"le lecteur ne peut pas les percevoir.")

    # ── Information loss ──
    if skipped:
        skipped_weight = sum(s["weight"] for s in skipped)
        total_weight = sum(p["weight"] for p in plan_vs_actual)
        loss_pct = skipped_weight / max(total_weight, 0.01)

        skipped_names = [f"'{s['name']}'" for s in skipped[:5]]
        paragraphs.append(
            f"Le lecteur n'a pas eu le temps de lire {loss_pct:.0%} de l'information "
            f"(calculé en poids des éléments), notamment {', '.join(skipped_names)}"
            f"{' et ' + str(len(skipped)-5) + ' autres' if len(skipped) > 5 else ''}.")

    # ── Attention concentration ──
    if heatmap and len(heatmap) > 1:
        total_att = sum(h["attention"] for h in heatmap)
        if total_att > 0:
            top = heatmap[0]
            top_pct = top["attention"] / total_att
            if top_pct > 0.4:
                paragraphs.append(
                    f"L'attention est concentrée : '{top['name']}' absorbe {top_pct:.0%} "
                    f"du temps total. Les éléments secondaires reçoivent peu d'attention "
                    f"en comparaison.")

    # ── Dead spaces ──
    if dead_spaces:
        names = [f"'{ds['name']}'" for ds in dead_spaces]
        paragraphs.append(
            f"Les zones {', '.join(names)} sont des zones mortes — "
            f"le regard n'y est jamais passé. Leur contenu est invisible "
            f"dans le temps imparti.")

    return "\n\n".join(paragraphs)


# ── CLI ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reader Simulation — proportional attention model")
    parser.add_argument("graph", help="Path to L3 graph YAML")
    parser.add_argument("--ticks", type=int, default=50, help="Simulation ticks (default 50 = 5s)")
    parser.add_argument("--system2", action="store_true",
                        help="System 2 mode: 90s budget (900 ticks) — deliberate reading")
    parser.add_argument("--verbose", "-v", action="store_true", help="Log each node visit")
    parser.add_argument("--debug", "-d", action="store_true", help="Full tick-by-tick trace")
    parser.add_argument("--output", "-o", help="Save results YAML")
    args = parser.parse_args()

    with open(args.graph) as f:
        graph = yaml.safe_load(f)

    sim_mode = "system2" if args.system2 else "system1"

    result = simulate_reading(
        graph, total_ticks=args.ticks,
        verbose=args.verbose, debug=args.debug,
        mode=sim_mode
    )

    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)

    # Print summary
    stats = result["stats"]
    print(f"\n{'='*60}")
    planned_ticks = 900 if args.system2 else args.ticks
    mode_label = "System 2 — deliberate" if args.system2 else "System 1 — glance"
    print(f"READER SIMULATION [{mode_label}] — simulates {stats['total_time_ms']/1000:.1f}s "
          f"({stats['total_ticks']}/{planned_ticks} ticks)")
    print(f"{'='*60}")
    print(f"Complexity: {stats['complexity_verdict']} "
          f"(pressure={stats['budget_pressure']:.2f}x)")
    print(f"Nodes visited: {stats['unique_nodes_visited']}/{stats['total_things']}"
          f" ({stats['nodes_skipped']} skipped)")
    print(f"Narrative coverage: {stats['narrative_coverage']:.0%}")
    print(f"Avg narrative attention: {stats['avg_narrative_attention']:.0%}")
    print(f"Dead spaces: {stats['dead_space_count']}")
    print(f"Orphan narratives: {stats['orphan_narrative_count']}")

    # Plan vs actual
    print(f"\n── PLAN vs ACTUAL ──")
    for p in result["plan_vs_actual"]:
        status = "✓" if p["status"] == "visited" else "✗"
        deficit = f" (deficit={p['deficit']})" if p["deficit"] > 0 else ""
        print(f"  {status} {p['node'][:35]:35s} | w={p['weight']:.2f} | "
              f"plan={p['planned_ticks']}t actual={p['actual_ticks']}t | "
              f"att={p['attention_received']:.3f}{deficit}")

    # Narrative details
    print(f"\n── NARRATIVES ──")
    for n in result["narrative_details"]:
        status = "✓" if n["status"] == "reached" else "✗"
        print(f"  {status} {n['received']:.0%} | {n['name'][:50]}")

    # Heatmap
    print(f"\n── HEATMAP (top 5) ──")
    for h in result["heatmap"][:5]:
        print(f"  {h['attention']:.3f} ({h['visits']}t, {h['pct']:.0%}) | {h['name'][:40]}")

    # Skipped nodes
    if result["skipped_nodes"]:
        print(f"\n── SKIPPED (never reached) ──")
        for s in result["skipped_nodes"]:
            print(f"  ✗ {s['name'][:40]:40s} | w={s['weight']:.2f}")

    # Reading narrative
    narrative_text = generate_reading_narrative(result, graph)
    print(f"\n── LECTURE SIMULÉE ──")
    print(narrative_text)

    # Recommendations (structured)
    if result["recommendations"]:
        print(f"\n── AXES D'AMÉLIORATION SUGGÉRÉS ──")
        for r in result["recommendations"]:
            print(f"\n  [{r['source']}]")
            print(f"  FAIT: {r['finding']}")
            print(f"  PROBLÈME: {r['problem']}")
            print(f"  QUESTION: {r['question']}")

    # Debug trace
    if args.debug and "debug_trace" in result:
        print(f"\n{'='*60}")
        print(f"DEBUG TRACE ({len(result['debug_trace'])} events)")
        print(f"{'='*60}")
        for event in result["debug_trace"]:
            phase = event["phase"]
            if phase == "PLAN":
                print(f"\n  ┌─ PLAN ─────────────────────────────────────────")
                print(f"  │ Budget: {event['total_ticks']} ticks = "
                      f"{event['fixation_budget']} fixation + {event['saccade_budget']} saccades")
                print(f"  │ Things: {event['total_things']} (total_weight={event['total_weight']})")
                for a in event["allocation"]:
                    bar = "█" * max(1, round(a["allocated"] * 2))
                    print(f"  │   {a['node'][:30]:30s} w={a['weight']:.2f} "
                          f"ideal={a['ideal']:5.1f} alloc={a['allocated']:2d} {bar}")
                print(f"  └────────────────────────────────────────────────")

            elif phase == "START":
                print(f"\n  t={event['tick']:3d} │ START → {event['first_node']} "
                      f"at {event['position']} (attention={event['attention']})")

            elif phase == "SACCADE":
                print(f"  t={event['tick']:3d} │ SACCADE {event['from']} → {event['to']} "
                      f"dist={event['distance']} → {event['target']}")

            elif phase == "FIXATION":
                narr_str = ""
                if "narrative_propagation" in event:
                    narr_parts = [
                        f"{n['narrative'][:25]}←{n['transmitted']}"
                        for n in event["narrative_propagation"]
                    ]
                    narr_str = f" ▸ {', '.join(narr_parts)}"
                print(f"  t={event['tick']:3d} │ FIX [{event['fixation_tick']}] "
                      f"{event['node'][:25]:25s} "
                      f"str={event['fixation_strength']} "
                      f"total={event['node_attention_total']}{narr_str}")

            elif phase == "TRUNCATED":
                print(f"  t={event['tick']:3d} │ ⚠ TRUNCATED {event['node']} "
                      f"({event['actual']}/{event['planned']} ticks)")

            elif phase == "TIMEOUT":
                print(f"  t={event['tick']:3d} │ ✗ TIMEOUT — skipped '{event['skipped_node']}' "
                      f"({event.get('reason', '')})")

            elif phase == "FINAL_ACCOUNTING":
                print(f"\n  ┌─ FINAL ACCOUNTING ──────────────────────────────")
                print(f"  │ Ticks: {event['ticks_used']}/{event['ticks_total']} "
                      f"(pressure={event['budget_pressure']}x)")
                print(f"  │ Nodes: {event['nodes_visited']} visited, "
                      f"{event['nodes_skipped']} skipped")
                print(f"  │ Narratives: {event['narratives_reached']}/{event['narratives_total']}")
                print(f"  │")
                for p in event["plan_vs_actual"]:
                    s = "✓" if p["status"] == "visited" else "✗"
                    print(f"  │ {s} {p['node'][:30]:30s} "
                          f"plan={p['planned_ticks']:2d} actual={p['actual_ticks']:2d} "
                          f"att={p['attention_received']:.3f}")
                print(f"  └───────────────────────────────────────────────")

    if args.output:
        # Remove debug_trace from YAML output (too verbose)
        output_data = {k: v for k, v in result.items() if k != "debug_trace"}
        with open(args.output, "w", encoding="utf-8") as f:
            yaml.dump(output_data, f, default_flow_style=False, allow_unicode=True)
        print(f"\nSaved: {args.output}")

        if args.debug:
            # Save debug trace separately as JSON (structured)
            debug_path = args.output.replace(".yaml", "_debug.json").replace(".yml", "_debug.json")
            with open(debug_path, "w", encoding="utf-8") as f:
                json.dump(result["debug_trace"], f, indent=2, ensure_ascii=False)
            print(f"Debug trace: {debug_path}")
